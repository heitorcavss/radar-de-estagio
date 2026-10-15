from .filtro import filtrar_vagas
from .dados_falsos import VAGAS_FALSAS  # temporário: sai quando a buscar_vagas usar o Adzuna

import os
import re
import unicodedata

import requests

URL_ADZUNA = "https://api.adzuna.com/v1/api/jobs/br/search/1"


def _chamar_adzuna(parametros: dict) -> dict:
    """Faz uma busca no Adzuna. Devolve {"status": "success", "total": n, "resultados": [...]}
    ou {"status": "error", "error_message": ...}.

    O try/except cobre só a chamada externa e captura só erros esperados (rede, HTTP, JSON).
    As mensagens são fixas de propósito: o texto de uma exceção do requests traz a URL com
    app_key, e a mensagem de erro chega ao modelo.
    """
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return {"status": "error", "error_message": "ADZUNA_APP_ID ou ADZUNA_APP_KEY não configurados no .env."}

    try:
        #esse format é o uso padrao do requests.get() url,params= (que monta a query string automaticamente), timeout
        response = requests.get(
            URL_ADZUNA,
            params={"app_id": app_id, "app_key": app_key, **parametros},
            timeout=15,
        )
        response.raise_for_status() #lança HTTPError se o status code não for 2xx
        dados = response.json()
    except requests.Timeout:
        return {"status": "error", "error_message": "O Adzuna demorou demais para responder."}
    except requests.ConnectionError:
        return {"status": "error", "error_message": "Não foi possível conectar ao Adzuna."}
    except requests.HTTPError as e:
        return {"status": "error", "error_message": f"O Adzuna respondeu com erro HTTP {e.response.status_code}."}
    except ValueError:  # resposta que não é JSON (JSONDecodeError herda de ValueError)
        return {"status": "error", "error_message": "O Adzuna devolveu uma resposta fora do formato esperado."}

    return {"status": "success", "total": dados.get("count", 0), "resultados": dados.get("results", [])}


LINGUAGENS_CONHECIDAS = ["Python", "Java", "JavaScript", "TypeScript", "PHP", "Ruby",
                         "Kotlin", "Swift", "Dart", "Scala", "C++", "C#"]

# Áreas detectadas só pelo título. A ordem importa: a primeira que casar vence.
AREAS_POR_PALAVRA = {
    "mobile": ["mobile", "android", "ios", "flutter", "react native"],
    "frontend": ["front-end", "frontend", "front end"],
    "ciberseguranca": ["ciberseguranca", "seguranca da informacao", "cybersecurity", "pentest"],
    "suporte_hardware": ["manutencao de computadores", "hardware"],
    "backend": ["backend", "back-end", "back end"],
    "ia": ["inteligencia artificial", "machine learning", "nlp", "ia"],
    "dados": ["dados", "data", "bi"],
    "cloud_devops": ["devops", "cloud", "infraestrutura"],
}


def _sem_acento(texto: str) -> str:
    """Minúsculas e sem acento, para 'híbrido' e 'hibrido' serem a mesma coisa."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def _tem_palavra(palavra: str, texto: str) -> bool:
    """True se a palavra aparece inteira no texto (já sem acento e minúsculo)."""
    return re.search(rf"\b{re.escape(palavra)}\b", texto) is not None


def _detectar_modalidade(texto: str) -> str | None:
    if "hibrido" in texto:  # primeiro: vagas híbridas costumam citar "remoto" também
        return "híbrido"
    if "remoto" in texto or "home office" in texto:
        return "remoto"
    if "presencial" in texto:
        return "presencial"
    return None  # desconhecida: o filtro mantém a vaga


def _detectar_area(titulo: str) -> str | None:
    titulo = _sem_acento(titulo)
    for area, palavras in AREAS_POR_PALAVRA.items():
        if any(_tem_palavra(p, titulo) for p in palavras):
            return area
    return None


def _detectar_linguagens(texto: str) -> list[str]:
    """Procura cada linguagem como palavra inteira. Os lookarounds impedem que 'Java'
    case dentro de 'JavaScript' e que 'C' case dentro de 'C++' ou 'C#'."""
    achadas = [nome for nome in LINGUAGENS_CONHECIDAS
               if re.search(rf"(?<![\w+#]){re.escape(nome)}(?![\w+#])", texto, re.IGNORECASE)]
    # "C" sozinho só vale maiúsculo, senão casaria com qualquer "c" solto
    if re.search(r"(?<![\w+#])C(?![\w+#])", texto):
        achadas.append("C")
    return achadas


def _converter_vaga(vaga: dict) -> dict:
    """Converte uma vaga do Adzuna para o formato interno. O que não dá para saber vira None."""
    titulo = vaga.get("title", "")
    descricao = vaga.get("description", "")
    cidade = vaga.get("location", {}).get("display_name", "").split(",")[0].strip()
    return {
        "id": vaga.get("id"),
        "titulo": titulo,
        "empresa": vaga.get("company", {}).get("display_name"),
        "cidade": None if cidade in ("", "Brasil") else cidade,
        "modalidade": _detectar_modalidade(_sem_acento(titulo + " " + descricao)),
        "area": _detectar_area(titulo),
        "linguagens": _detectar_linguagens(titulo + " " + descricao),
        "descricao": descricao,
        "url": vaga.get("redirect_url"),
    }


def buscar_vagas(termos_de_busca: list[str] | None = None) -> dict:
    """
    Lista vagas de estágio de TI da base de vagas disponível, por tema.
    Já devolve só vagas que passam nas regras eliminatórias (local, área e linguagem).
    
    Use quando o usuário pedir vagas, estágios ou oportunidades, com ou sem
    um tema. Não use para perguntas gerais (por exemplo, "o que é um agente
    de IA?"). Esta função só lista vagas: não avalia se combinam com o
    usuário nem envia candidatura.
    
    Args:
        termos_de_busca: Termos para procurar nas vagas. Uma vaga é devolvida
        se contiver qualquer um dos termos. Inclua sinônimos e termos
        relacionados de cada tema pedido. Se o usuário pedir mais de um
        tema, junte todos na mesma lista. Exemplos:
        "IA" -> ["IA", "machine learning", "NLP", "MLOps"];
        "backend" -> ["backend", "Python", "Java", "API"].
        Se omitido, devolve todas as vagas.
    Returns:
        Um dicionário com:
        - "status": "success" ou "error".
        - "numero_vagas": quantidade de vagas devolvidas (pode ser 0, o que
          significa que nenhuma vaga combinou, não que houve erro).
        - "vagas": lista de vagas. Cada vaga tem id, titulo, empresa,
          cidade, modalidade (remoto, híbrido ou presencial), area,
          linguagens, requisitos, ingles, semestre_minimo e url.
        - "error_message": só aparece se "status" for "error".
    """
    encontradas = []
    # o filtro roda antes da busca: só vagas que passam nas regras entram
    vagas_validas = filtrar_vagas(VAGAS_FALSAS)
    
    # Implementação da função de busca de vagas
    try:
        #protetor: se não houver termos de busca, devolve todas as vagas
        if not termos_de_busca:
            return {"numero_vagas": len(vagas_validas), "vagas": vagas_validas, "status": "success"}
        #protetor: se termos_de_busca não for uma lista, lança ValueError
        if not isinstance(termos_de_busca, list):
            raise ValueError("termos_de_busca deve ser uma lista de strings.")
        
        #preparação de termos: tudo minusculo e separar palavras como 'machine learning' em ['machine', 'learning']
        termos_em_palavras = [termo.lower().split() for termo in termos_de_busca]
        for vaga in vagas_validas: # pega 1 vaga por vez
            
            # para cada vaga, cria se uma lista de palavras com .split() e .lower() para comparar com os termos de busca.
            # usa-se " ".join() para juntar as listas de linguagens e requisitos em uma única string, que depois é dividida em palavras.
            # campos: titulo, area, linguagens, requisitos
            palavras_vaga = (vaga["titulo"] + " " + vaga["area"] + " " + " ".join(vaga["linguagens"]) + " " + " ".join(vaga["requisitos"])).lower().split()
            
            
            for termo in termos_em_palavras: # para cada termo tratado em termos_em_palavras, 
                 #termo = 'python' (exemplo agora)
                termo_casou = True
                for palavra in termo: # para cada palavra em 'python' (ele mesmo)
                    if palavra not in palavras_vaga: # verificamos se a palavra do termo esta na lista de palavras da vaga. 
                        # caso sim, add à lista de encontradas e break para não procurar mais nesse termo
                        termo_casou = False
                if termo_casou:
                    encontradas.append(vaga)
                    break

    except Exception as e:
        return {"numero_vagas": 0, "vagas": [], "status": "error", "error_message": str(e)}
    
    return {"numero_vagas": len(encontradas), "vagas": encontradas, "status": "success"}

if __name__ == "__main__":
    resultado = buscar_vagas(["Cybersecurity", "Cibersecurity", "Cibersegurança", "Ciberseguranca", "Segurança da Informação", "Segurança da informacao"])
    print(resultado)
    