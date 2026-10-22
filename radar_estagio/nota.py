"""Nota de compatibilidade entre vaga e perfil, por palavras-chave.

Sem modelo e sem cache: a mesma vaga e o mesmo perfil dão sempre a mesma nota.
Limite: só enxerga as tecnologias que estão em TECNOLOGIAS (as linguagens vêm do detector do tools.py).
"""
import re

from .tools import _sem_acento, _tem_palavra

PESO_TECNOLOGIAS = 70
PESO_AREA = 30
NOTA_MAX_ELIMINATORIA = 60
NOTA_MAX_FORA_DO_OBJETIVO = 50
NOTA_PARCIAL = 0.5  # habilidade "em estudo" cobre metade do requisito
MIN_PESO_PEDIDO = 4  # a parte das tecnologias divide por max(soma dos pesos pedidos, isto): subir pesa menos vaga que pede pouca coisa
PESOS = {"python": 3, "fastapi": 2, "llms": 2, "sql": 2}  # tecnologias do objetivo valem mais; as demais valem PESO_PADRAO
PESO_PADRAO = 1
SEM_REQUISITOS = 0.3  # vaga sem tecnologia reconhecida: pouca informação, parte das tecnologias fica baixa
PONTOS_AREA = {"backend": 1.0, "ia": 1.0, "dados": 0.6, "cloud_devops": 0.6}
PONTOS_AREA_DESCONHECIDA = 0.5  # título sem área detectada (ex.: "Estágio em Desenvolvimento")
FORA_DO_OBJETIVO = ["suporte", "help desk", "helpdesk", "atendimento", "vendas"]  # palavras do título

# Nome no perfil (sem acento, minúsculo) -> como a vaga escreve. Outras linguagens vêm de vaga["linguagens"].
# "sql server" vem antes de "sql": o trecho achado sai do texto, então "SQL Server" não conta como "SQL".
TECNOLOGIAS = {
    "sql server": ["sql server"], "banco de dados vetorial": ["banco de dados vetorial", "bancos de dados vetoriais"],
    "sql": ["sql"], "postgresql": ["postgresql", "postgres", "postgre"],
    "mongodb": ["mongodb"], "redis": ["redis"],
    "fastapi": ["fastapi"], "flask": ["flask"], "django": ["django"], "sqlalchemy": ["sqlalchemy"],
    "api rest": ["api rest", "apis rest", "rest api", "rest apis", "restful"],
    "docker": ["docker"], "git": ["git"], "github": ["github"], "linux": ["linux"],
    "kubernetes": ["kubernetes"], "aws": ["aws"], "azure": ["azure"], "ci/cd": ["ci/cd"],
    "spring": ["spring"], "react": ["react", "reactjs"], "html": ["html"], "css": ["css"],
    "llms": ["llm", "llms"], "nlp": ["nlp"], "machine learning": ["machine learning"],
    "pandas": ["pandas"], "numpy": ["numpy"], "pytorch": ["pytorch"], "tensorflow": ["tensorflow"],
    "power bi": ["power bi"], "excel": ["excel"],
}

# Frases genéricas que contam como uma tecnologia do perfil: frase (sem acento) -> (tecnologia, frase para mostrar).
# Na resposta aparece a frase da vaga, para não parecer que ela pediu a tecnologia pelo nome.
GENERICOS = {"banco de dados": ("sql", "banco de dados"), "bancos de dados": ("sql", "bancos de dados"),
             "logica de programacao": ("python", "lógica de programação")}


def calcular_nota(vaga: dict, perfil: dict) -> dict:
    """70% tecnologias (peso das pedidas que o perfil cobre; Python e IA/backend pesam mais) + 30% área, com tetos para exigência
    eliminatória (período, graduação concluída) e para vaga fora do objetivo (suporte, vendas)."""
    titulo = _sem_acento(vaga["titulo"])
    descricao = _sem_acento(vaga["descricao"])

    # tecnologias que a vaga cita: {nome: como mostrar}
    texto = titulo + " " + descricao
    # "cursando A, B, C, D..." é a lista de cursos aceitos, não requisito (ex.: "Inteligência Artificial e Machine Learning")
    texto = re.sub(r"cursando[^\n.]*", lambda m: " " if m.group().count(",") >= 4 else m.group(), texto)
    achadas = {_sem_acento(l): l for l in vaga["linguagens"]}
    for nome, apelidos in TECNOLOGIAS.items():
        for apelido in apelidos:
            if _tem_palavra(apelido, texto):
                achadas.setdefault(nome, nome)
                texto = re.sub(rf"\b{re.escape(apelido)}\b", " ", texto)  # tira do texto o que já foi contado
    for frase, (nome, rotulo) in GENERICOS.items():
        if _tem_palavra(frase, texto):
            achadas.setdefault(nome, f'{nome} ("{rotulo}")')  # se a vaga já cita a tecnologia pelo nome, fica o nome

    # o que o perfil cobre (habilidades e tecnologias dos projetos) e o que está em estudo
    completas = {_sem_acento(h) for lista in perfil["habilidades"].values() for h in lista}
    completas |= {_sem_acento(t) for p in perfil["projetos"] for t in p["tecnologias"]}
    completas.add("api rest")  # o perfil escreve "APIs REST" nas habilidades e "API REST" nos projetos
    parciais = {_sem_acento(h) for h in perfil["habilidades_parciais"]}

    tem = [rotulo for nome, rotulo in achadas.items() if nome in completas]
    em_estudo = [rotulo for nome, rotulo in achadas.items() if nome in parciais]
    lacunas = [rotulo for nome, rotulo in achadas.items() if nome not in completas and nome not in parciais]

    sem_requisitos = not achadas
    peso = lambda nome: PESOS.get(nome, PESO_PADRAO)
    peso_pedido = sum(peso(nome) for nome in achadas)
    peso_coberto = sum(peso(nome) for nome in achadas if nome in completas) + NOTA_PARCIAL * sum(peso(nome) for nome in achadas if nome in parciais)
    parte_tecnologias = SEM_REQUISITOS if sem_requisitos else peso_coberto / max(peso_pedido, MIN_PESO_PEDIDO)
    fora_do_objetivo = any(_tem_palavra(p, titulo) for p in FORA_DO_OBJETIVO)
    pontos_area = 0.0 if fora_do_objetivo else PONTOS_AREA.get(vaga["area"], PONTOS_AREA_DESCONHECIDA)
    nota = PESO_TECNOLOGIAS * parte_tecnologias + PESO_AREA * pontos_area

    # exigências que o usuário não cumpre hoje
    atencao = []
    periodo = re.search(r"(\d{1,2})\s*o?\s*(?:ao?\s+\d{1,2}\s*o?\s*)?(?:periodo|semestre)", descricao)  # "5º período", "3º ao 6º período"
    if periodo and int(periodo.group(1)) > perfil["formacao"]["periodo_atual"]:
        atencao.append(f"exige {periodo.group(1)}º período (você está no {perfil['formacao']['periodo_atual']}º)")
    if "graduacao concluida" in descricao or _tem_palavra("graduado", titulo):
        atencao.append("exige graduação concluída")
    if atencao:
        nota = min(nota, NOTA_MAX_ELIMINATORIA)
    if fora_do_objetivo:
        nota = min(nota, NOTA_MAX_FORA_DO_OBJETIVO)

    return {"nota": int(nota + 0.5), "voce_ja_tem": tem, "em_estudo": em_estudo, "lacunas": lacunas,
            "atencao": atencao, "sem_requisitos_claros": sem_requisitos}


def avaliar_vagas(vagas: list[dict], perfil: dict) -> None:
    """Põe a chave "compatibilidade" em cada vaga e ordena da maior nota para a menor."""
    for vaga in vagas:
        vaga["compatibilidade"] = calcular_nota(vaga, perfil)
    vagas.sort(key=lambda v: -v["compatibilidade"]["nota"])
