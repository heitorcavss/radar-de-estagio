from .filtro import filtrar_vagas

import json
import os
import re
import time
import unicodedata
from pathlib import Path

import requests

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
# Nomes de curso ("ciência da computação", "engenharia de software") ficam de fora: anúncios de
# qualquer área listam quem pode se candidatar, e isso deixou passar uma vaga de vendas (Auvo).
TERMOS_TI_DESCRICAO = ["programacao", "python", "java", "javascript", "sql", "tecnologia da informacao",
                       "desenvolvimento de software", "analise de sistemas", "banco de dados",
                       "ciencia de dados", "engenharia de dados", "machine learning"]


def _sem_acento(texto: str) -> str:
    """Minúsculas e sem acento, para 'estágio' e 'estagio' serem a mesma coisa."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def _tem_palavra(palavra: str, texto: str) -> bool:
    """True se a palavra aparece inteira no texto (já sem acento e minúsculo)."""
    return re.search(rf"\b{re.escape(palavra)}\b", texto) is not None


def _detectar_ti(titulo: str, descricao: str) -> bool:
    """True se o título tem um termo de TI ou a descrição tem um termo específico de TI.
    Muitos estágios de TI não dizem isso no título, por isso a descrição também conta."""
    titulo = _sem_acento(titulo)
    descricao = _sem_acento(descricao)
    return (any(_tem_palavra(p, titulo) for p in TERMOS_TI_TITULO)
            or any(_tem_palavra(p, descricao) for p in TERMOS_TI_DESCRICAO))


ANOS_MINIMOS_EXPERIENCIA = 2  # 1 ano ainda aparece em anúncios de estágio; 2 ou mais não
PADROES_EXPERIENCIA = [
    r"(\d+)\+?\s*(?:anos|years?)\s+(?:de\s+|of\s+)?(?:experiencia|experience)",  # "5+ years of experience"
    r"experiencia\s+(?:minima\s+)?(?:de\s+)?(\d+)\+?\s*(?:anos|years?)",  # "experiência de 3 anos"
]


PALAVRAS_SOBRE_EMPRESA = ["empresa", "somos", "temos", "nossa", "our ", "we ", "company"]


def _exige_experiencia(titulo: str, descricao: str) -> bool:
    """True se o título diz pleno/sênior/auxiliar/aprendiz ou a descrição pede
    ANOS_MINIMOS_EXPERIENCIA ou mais anos de experiência. Meses e "experiência" sem número
    não contam."""
    titulo = _sem_acento(titulo)
    if any(_tem_palavra(p, titulo) for p in ("senior", "pleno", "sr", "auxiliar", "aprendiz")):
        return True
    descricao = _sem_acento(descricao)
    for padrao in PADROES_EXPERIENCIA:
        for m in re.finditer(padrao, descricao):
            antes = descricao[max(0, m.start() - 60):m.start()]
            # "somos uma empresa com mais de 20 anos de experiência" fala da empresa, não da vaga
            if any(p in antes for p in PALAVRAS_SOBRE_EMPRESA):
                continue
            if int(m.group(1)) >= ANOS_MINIMOS_EXPERIENCIA:
                return True
    return False


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


URL_SERPAPI = "https://serpapi.com/search"
LOCAL_SERPAPI = "Goiânia, State of Goiás, Brazil"
MAX_TERMOS = 3  # cada termo é 1 busca (1 das 250 do mês no plano grátis): limita o gasto
PAUSA_ENTRE_BUSCAS = 0.5  # segundos


def _chamar_serpapi(q: str) -> dict:
    """Faz uma busca no Google Jobs via SerpApi. Devolve {"status": "success", "resultados": [...]}
    ou {"status": "error", "error_message": ...}.
    Mensagens fixas: o texto de uma exceção do requests traz a URL com a api_key."""
    chave = os.environ.get("SERPAPI_KEY")
    if not chave:
        return {"status": "error", "error_message": "SERPAPI_KEY não configurada no .env."}

    try:
        response = requests.get(
            URL_SERPAPI,
            params={"engine": "google_jobs", "q": q, "location": LOCAL_SERPAPI,
                    "hl": "pt", "gl": "br", "api_key": chave},
            timeout=30,
        )
        response.raise_for_status()
        dados = response.json()
    except requests.Timeout:
        return {"status": "error", "error_message": "A SerpApi demorou demais para responder."}
    except requests.ConnectionError:
        return {"status": "error", "error_message": "Não foi possível conectar à SerpApi."}
    except requests.HTTPError as e:
        return {"status": "error", "error_message": f"A SerpApi respondeu com erro HTTP {e.response.status_code}."}
    except ValueError:
        return {"status": "error", "error_message": "A SerpApi devolveu uma resposta fora do formato esperado."}

    erro = dados.get("error")
    # "nenhum resultado" vem como erro com status 200: para nós é busca vazia, não falha
    if erro and "hasn't returned any results" not in erro:
        return {"status": "error", "error_message": "A SerpApi devolveu um erro."}
    return {"status": "success", "resultados": dados.get("jobs_results", [])}


def _converter_vaga_serpapi(vaga: dict) -> dict:
    """Converte uma vaga do Google Jobs (SerpApi) para o formato interno.
    Modalidade: 'Trabalho de casa' nas extensões ou local 'Qualquer lugar' = remoto.
    Estágio: extensão 'Estágio' ou a palavra no título/descrição."""
    titulo = vaga.get("title", "")
    descricao = vaga.get("description", "")
    extensoes = vaga.get("extensions") or []
    local = vaga.get("location") or ""
    remoto = "Trabalho de casa" in extensoes or local == "Qualquer lugar"
    # "Goiânia, GO" e "Goiânia - GO": a cidade é o que vem antes da vírgula ou do hífen
    cidade = re.split(r",| - ", local)[0].strip()
    ligacoes = vaga.get("apply_options") or []
    url = (ligacoes[0].get("link") if ligacoes else None) or vaga.get("source_link") or vaga.get("share_link")
    return {
        "id": vaga.get("job_id"),
        "titulo": titulo,
        "empresa": vaga.get("company_name") or None,
        "cidade": None if cidade in ("", "Qualquer lugar") else cidade,
        "modalidade": "remoto" if remoto else None,
        "area": _detectar_area(titulo),
        "ti": _detectar_ti(titulo, descricao),
        "estagio": "Estágio" in extensoes or _tem_palavra("estagio", _sem_acento(titulo)) or
                   _tem_palavra("estagiario", _sem_acento(titulo)) or
                   _tem_palavra("estagiaria", _sem_acento(titulo)) or
                   _tem_palavra("estagio", _sem_acento(descricao)),
        "exige_experiencia": _exige_experiencia(titulo, descricao),
        "linguagens": _detectar_linguagens(titulo + " " + descricao),
        "descricao": descricao,
        "url": url,
    }


# Termos usados quando o usuário não dá tema. Medidos no SerpApi: "estágio TI Goiânia" (7 vagas),
# "estágio dados Goiânia" (5) e "estagiário programação Goiânia" (10). "python" sozinho zerou.
TERMOS_BUSCA_PADRAO = ["TI", "dados", "programação"]
TEMA_REMOTO_PADRAO = "desenvolvedor"  # "estágio desenvolvedor remoto" trouxe 10 vagas remotas


def buscar_vagas(termos_de_busca: list[str] | None = None) -> dict:
    """
    Busca vagas de estágio de TI reais (Google Jobs), em Goiânia e região ou remotas.
    Já devolve só vagas que passam nas regras eliminatórias (estágio, local, área,
    linguagem e relevância de TI).

    Use quando o usuário pedir vagas, estágios ou oportunidades, com ou sem
    um tema. Não use para perguntas gerais (por exemplo, "o que é um agente
    de IA?"). Esta função só lista vagas: não avalia se combinam com o
    usuário nem envia candidatura.

    Args:
        termos_de_busca: Termos do tema pedido. Cada termo vira uma busca separada
        ("estágio <termo> Goiânia"), e só os 3 primeiros são usados, então coloque
        o mais importante primeiro. Use termos curtos e comuns em anúncios (por
        exemplo "dados", "backend", "inteligência artificial"); termos muito
        específicos, como o nome de uma biblioteca, costumam não achar nada. Se o
        tema não for de TI (por exemplo, "astronauta"), passe só o termo dele, sem
        acrescentar termos de TI. Se o usuário pedir mais de um tema, junte todos
        na mesma lista. Exemplo: para "ciência de dados", use ["ciência de dados",
        "dados", "analytics"].
        Se o usuário não pedir um tema, NÃO passe este argumento: a função já
        busca estágios de TI em geral.
    Returns:
        Um dicionário com:
        - "status": "success" ou "error".
        - "numero_vagas": quantidade de vagas devolvidas (pode ser 0, o que
          significa que nenhuma vaga combinou, não que houve erro).
        - "vagas": lista de vagas. Cada vaga tem id, titulo, empresa (pode ser
          vazia), cidade (pode ser vazia), modalidade (remoto, híbrido,
          presencial ou vazia), area (pode ser vazia), ti, linguagens,
          descricao e url. Campos vazios significam que não deu para saber.
          Também traz nota de compatibilidade e "nova": verdadeiro se a vaga
          ainda não estava salva no banco (falso se já tinha aparecido antes;
          ausente se o banco falhou).
        - "error_message": só aparece se "status" for "error".
    """
    # validação da entrada
    if termos_de_busca is not None and not isinstance(termos_de_busca, list):
        return {"numero_vagas": 0, "vagas": [], "status": "error",
                "error_message": "termos_de_busca deve ser uma lista de strings."}

    # sem tema, usa os termos padrão; cada termo é uma busca em Goiânia, mais uma busca remota
    termos = [t for t in (termos_de_busca or TERMOS_BUSCA_PADRAO) if isinstance(t, str) and t.strip()]
    termos = (termos or TERMOS_BUSCA_PADRAO)[:MAX_TERMOS]
    tema_remoto = termos_de_busca[0] if termos_de_busca else TEMA_REMOTO_PADRAO
    buscas = [f"estágio {t} Goiânia" for t in termos] + [f"estágio {tema_remoto} remoto"]

    respostas = []
    for i, q in enumerate(buscas):
        if i > 0:
            time.sleep(PAUSA_ENTRE_BUSCAS)
        respostas.append(_chamar_serpapi(q))
    sucessos = [r for r in respostas if r["status"] == "success"]
    if not sucessos:  # todas falharam
        return {"numero_vagas": 0, "vagas": [], "status": "error",
                "error_message": respostas[0]["error_message"]}

    # junta as listas sem repetir: a mesma vaga aparece com ids diferentes em sites diferentes,
    # então a chave é título + empresa
    unicas = {}
    for resposta in sucessos:
        for vaga in resposta["resultados"]:
            chave = (_sem_acento(vaga.get("title", "")), _sem_acento(vaga.get("company_name") or ""))
            unicas.setdefault(chave, vaga)

    convertidas = [_converter_vaga_serpapi(v) for v in unicas.values()]
    vagas = filtrar_vagas(convertidas)
    from .nota import avaliar_vagas  # aqui dentro: o nota.py importa helpers deste arquivo (evita import circular)

    perfil = carregar_perfil()
    if vagas and perfil["status"] == "success":
        avaliar_vagas(vagas, perfil["perfil"])  # põe a nota em cada vaga e ordena
    if vagas:
        from .banco import salvar_vagas  # aqui dentro: importar o banco cria o arquivo .db
        from sqlalchemy.exc import SQLAlchemyError
        try:
            salvar_vagas(vagas)  # põe "nova" em cada vaga
        except SQLAlchemyError:
            pass  # o banco não pode derrubar a busca: as vagas voltam sem o campo "nova"
    return {"numero_vagas": len(vagas), "vagas": vagas, "status": "success"}


CAMINHO_PERFIL = Path(__file__).parent / "perfil.json"


def carregar_perfil() -> dict:
    """
    Devolve o perfil do usuário (formação, habilidades, projetos), tirado do currículo.

    Use antes de avaliar a compatibilidade de vagas com o usuário. Não precisa de
    argumentos e não usa a internet, então pode ser chamada uma vez por conversa.

    Returns:
        Um dicionário com:
        - "status": "success" ou "error".
        - "perfil": os dados do perfil (só quando o status é "success").
        - "error_message": o motivo, quando o status é "error".
    """
    try:
        with open(CAMINHO_PERFIL, encoding="utf-8") as arquivo:
            return {"status": "success", "perfil": json.load(arquivo)}
    except FileNotFoundError:
        return {"status": "error", "error_message": "O arquivo perfil.json não foi encontrado."}
    except json.JSONDecodeError:
        return {"status": "error", "error_message": "O arquivo perfil.json está com formato inválido."}


def listar_vagas_salvas(area: str | None = None, modalidade: str | None = None, limite: int = 20) -> dict:
    """
    Lista vagas que JÁ foram encontradas e salvas antes, sem fazer uma busca nova
    (não gasta busca na internet). Use quando o usuário perguntar o que já foi visto,
    pedir para rever vagas salvas ou pedir um filtro sobre elas.
    Não use para procurar vagas novas: isso é `buscar_vagas`.

    Args:
        area: Filtra pela área da vaga. Use exatamente um destes valores: "backend",
        "frontend", "mobile", "ia", "dados", "cloud_devops", "ciberseguranca",
        "suporte_hardware". Omita para não filtrar.
        modalidade: Use "remoto" para só vagas remotas. Omita para não filtrar.
        limite: Máximo de vagas devolvidas (padrão 20).
    Returns:
        Um dicionário com "status" ("success" ou "error"), "numero_vagas" e "vagas" (as
        mais recentes primeiro, depois reordenadas pela nota de compatibilidade). Cada vaga
        tem os mesmos campos da `buscar_vagas`, sem o campo "nova". Se o banco falhar,
        vem "error_message".
    """
    
    from .banco import consultar_vagas
    from .nota import avaliar_vagas
    from sqlalchemy.exc import SQLAlchemyError
    
    try:
        vagas = consultar_vagas(area, modalidade, limite)
    except SQLAlchemyError:
        return {"numero_vagas": 0, "vagas": [], "status": "error",
                "error_message": "Falha ao acessar o banco de vagas salvas."}
        
    perfil = carregar_perfil()
    if vagas and perfil["status"] == "success":
        avaliar_vagas(vagas, perfil["perfil"])  # põe a nota em cada vaga e ordena

    return {"numero_vagas": len(vagas), "vagas": vagas, "status": "success"}

def analisar_vaga(titulo: str, descricao: str) -> dict:
    """
    Analisa UMA vaga que o usuário colou na conversa e diz o quanto ela combina com o
    perfil dele: nota, o que ele já tem, o que está em estudo e as lacunas.
    Não faz busca na internet e não salva nada. Use quando o usuário trouxer o texto de uma
    vaga e pedir para avaliá-la. Para procurar vagas, use `buscar_vagas`.

    Args:
        titulo: O título da vaga, como o usuário informou. Se ele não disse o título,
        pergunte antes de chamar.
        descricao: O texto completo da vaga (requisitos, tecnologias, exigências).
    Returns:
        Um dicionário com "status" ("success" ou "error"). Em "success", traz
        "compatibilidade" com os mesmos campos da `buscar_vagas` (nota, voce_ja_tem,
        em_estudo, lacunas, atencao, sem_requisitos_claros). Em "error", traz "error_message".
    """
    from .nota import calcular_nota  # aqui dentro: o nota.py importa helpers deste arquivo (evita import circular)

    if not titulo.strip() or not descricao.strip():
        return {"status": "error", "error_message": "Preciso do título e da descrição da vaga."}

    perfil = carregar_perfil()
    if perfil["status"] != "success":
        return perfil

    vaga = {"titulo": titulo, "descricao": descricao, "area": _detectar_area(titulo),
            "linguagens": _detectar_linguagens(titulo + " " + descricao)}
    return {"status": "success", "compatibilidade": calcular_nota(vaga, perfil["perfil"])}


if __name__ == "__main__":
    # rodar com: python -m radar_estagio.tools  (gasta 4 das 250 buscas do mês na SerpApi)
    from dotenv import load_dotenv

    load_dotenv("radar_estagio/.env")
    resultado = buscar_vagas()
    print(resultado["status"], resultado["numero_vagas"])
    for vaga in resultado["vagas"]:
        print("-", vaga["titulo"], "|", vaga["cidade"], "|", vaga["modalidade"], "|", vaga["linguagens"])
        print("  ", vaga["url"])
