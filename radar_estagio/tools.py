from .filtro import filtrar_vagas
from .dados_falsos import VAGAS_FALSAS  # temporário: sai quando a buscar_vagas usar o Adzuna

import os

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
    