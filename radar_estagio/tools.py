from .filtro import filtrar_vagas

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


# Termos que indicam vaga de TI. No título bastam termos curtos; na descrição só termos
TERMOS_TI_TITULO = ["ti", "tecnologia", "software", "dados", "desenvolvedor", "desenvolvimento",
                    "programacao", "sistemas", "computacao", "informatica", "dev", "devops",
                    "cloud", "backend", "back-end", "ia", "inteligencia artificial", "bi", "data",
                    "analytics", "infraestrutura", "redes", "suporte tecnico", "banco de dados"]
TERMOS_TI_DESCRICAO = ["programacao", "python", "java", "sql", "tecnologia da informacao",
                       "desenvolvimento de software", "ciencia da computacao", "engenharia de software",
                       "engenharia da computacao", "analise de sistemas", "banco de dados",
                       "ciencia de dados", "engenharia de dados", "machine learning"]


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


def _detectar_ti(titulo: str, descricao: str) -> bool:
    """True se o título tem um termo de TI ou a descrição tem um termo específico de TI.
    Muitos estágios de TI não dizem isso no título, por isso a descrição também conta."""
    titulo = _sem_acento(titulo)
    descricao = _sem_acento(descricao)
    return (any(_tem_palavra(p, titulo) for p in TERMOS_TI_TITULO)
            or any(_tem_palavra(p, descricao) for p in TERMOS_TI_DESCRICAO))


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
        "ti": _detectar_ti(titulo, descricao),
        "linguagens": _detectar_linguagens(titulo + " " + descricao),
        "descricao": descricao,
        "url": vaga.get("redirect_url"),
    }


# Termos usados quando o usuário não dá tema. Específicos de TI e ligados aos interesses
# (backend, IA, dados): termos curtos como "ti" trazem ruído. O filtro barra o que sobrar de fora.
TERMOS_BUSCA_PADRAO = ["python", "java", "backend", "desenvolvedor", "dados",
                       "inteligência artificial", "programação"]

BUSCA_GOIANIA = {"where": "Goiânia", "distance": 30}  # 30 km cobre Goiânia e Aparecida de Goiânia


def buscar_vagas(termos_de_busca: list[str] | None = None) -> dict:
    """
    Busca vagas de estágio de TI reais (Adzuna), em Goiânia e região ou remotas.
    Já devolve só vagas que passam nas regras eliminatórias (local, área, linguagem
    e relevância de TI).

    Use quando o usuário pedir vagas, estágios ou oportunidades, com ou sem
    um tema. Não use para perguntas gerais (por exemplo, "o que é um agente
    de IA?"). Esta função só lista vagas: não avalia se combinam com o
    usuário nem envia candidatura.

    Args:
        termos_de_busca: Termos do tema pedido. Uma vaga é devolvida se contiver
        qualquer um dos termos (no título ou na descrição), então cada termo
        a mais deixa a busca mais larga. Use só sinônimos diretos do tema, no
        máximo 5 termos. NUNCA use termos genéricos de TI (software, tecnologia,
        desenvolvimento, engenharia, TI), porque eles casam com quase toda vaga
        e trazem vagas sem relação com o tema. Se o tema não for de TI (por
        exemplo, "astronauta"), passe só os termos dele, sem acrescentar termos
        de TI. Se o usuário pedir mais de um tema, junte todos na mesma lista.
        Exemplo: para "ciência de dados", use ["dados", "data science", "analytics"].
        Se omitido, devolve estágios de TI em geral.
    Returns:
        Um dicionário com:
        - "status": "success" ou "error".
        - "numero_vagas": quantidade de vagas devolvidas (pode ser 0, o que
          significa que nenhuma vaga combinou, não que houve erro).
        - "vagas": lista de vagas. Cada vaga tem id, titulo, empresa (pode ser
          vazia), cidade (pode ser vazia), modalidade (remoto, híbrido,
          presencial ou vazia), area (pode ser vazia), ti, linguagens,
          descricao e url. Campos vazios significam que não deu para saber.
        - "error_message": só aparece se "status" for "error".
    """
    # validação da entrada
    if termos_de_busca is not None and not isinstance(termos_de_busca, list):
        return {"numero_vagas": 0, "vagas": [], "status": "error",
                "error_message": "termos_de_busca deve ser uma lista de strings."}

    # sem tema, usa os termos padrão: sem what_or o Adzuna traz 50 estágios de todas as áreas
    termos = termos_de_busca or TERMOS_BUSCA_PADRAO
    base = {"what": "estágio", "results_per_page": 50,
            "what_or": " ".join(termos)}  # o Adzuna separa por espaço e aceita qualquer um

    # duas buscas: perto de Goiânia, e remotas de qualquer cidade
    respostas = [
        _chamar_adzuna({**base, **BUSCA_GOIANIA}),
        _chamar_adzuna({**base, "what": "estágio remoto"}),
    ]
    sucessos = [r for r in respostas if r["status"] == "success"]
    if not sucessos:  # as duas falharam
        return {"numero_vagas": 0, "vagas": [], "status": "error",
                "error_message": respostas[0]["error_message"]}

    # junta as duas listas sem repetir a mesma vaga (pelo id), mantendo a ordem
    por_id = {}
    for resposta in sucessos:
        for vaga in resposta["resultados"]:
            por_id.setdefault(vaga["id"], vaga)

    convertidas = [_converter_vaga(v) for v in por_id.values()]
    vagas = filtrar_vagas(convertidas)
    return {"numero_vagas": len(vagas), "vagas": vagas, "status": "success"}


if __name__ == "__main__":
    # rodar com: python -m radar_estagio.tools  (gasta 2 chamadas da cota do Adzuna)
    from dotenv import load_dotenv

    load_dotenv("radar_estagio/.env")
    resultado = buscar_vagas(["python", "java", "desenvolvedor"])
    print(resultado["status"], resultado["numero_vagas"])
    for vaga in resultado["vagas"]:
        print("-", vaga["titulo"], "|", vaga["cidade"], "|", vaga["modalidade"], "|", vaga["linguagens"])
        print("  ", vaga["url"])
