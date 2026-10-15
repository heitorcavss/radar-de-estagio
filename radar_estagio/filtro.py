# Goiânia e Aparecida de Goiânia.
CIDADES_BASE = {"Goiânia", "Aparecida de Goiânia"}
AREAS_EXCLUIDAS = {"suporte_hardware", "ciberseguranca", "frontend", "mobile"}
# Áreas em que o estágio é de programação: exigem Java, Python ou C.
AREAS_DEV = {"backend", "fullstack", "embarcados", "ia"}
LINGUAGENS_ACEITAS = {"java", "python", "c"}


def passa_no_filtro(vaga: dict) -> bool:
    """Regras eliminatórias: devolve True se a vaga pode seguir para a análise.

    Na dúvida (campo None), a vaga fica. Só barra quando há certeza.
    """
    if vaga["area"] in AREAS_EXCLUIDAS:
        return False

    # Cidade conhecida e fora da base: só passa se for remota.
    # Cidade desconhecida: mantém.
    # Sem nenhum sinal de TI no título nem na descrição: barra (Farmácia, Contábil...).
    # .get porque os dados falsos antigos não têm o campo "ti"; sem o campo, mantém.
    if vaga.get("ti") is False:
        return False

    cidade = vaga["cidade"]
    if cidade is not None and cidade not in CIDADES_BASE and vaga["modalidade"] != "remoto":
        return False

    # Linguagem: só barra se a vaga cita linguagens e nenhuma é aceita.
    # Vale para áreas de programação e para área desconhecida, tipo, dados e cloud não exigem linguagem.
    linguagens = {l.lower() for l in vaga["linguagens"]}
    if linguagens and (vaga["area"] is None or vaga["area"] in AREAS_DEV):
        if not linguagens & LINGUAGENS_ACEITAS:  # & = interseção; vazia = nenhuma linguagem aceita
            return False

    return True


def filtrar_vagas(vagas: list[dict]) -> list[dict]:
    return [v for v in vagas if passa_no_filtro(v)]


if __name__ == "__main__":
    from .dados_falsos import VAGAS_FALSAS

    falhas = []

    # 1- Dados falsos (formato antigo, mesmas chaves): mesmo resultado de antes.
    esperado = {1, 2, 3, 4, 6, 9, 13, 15, 16}  # vagas sem "BARRADA" nos comentários de dados_falsos.py
    obtido = {v["id"] for v in filtrar_vagas(VAGAS_FALSAS)}
    if obtido != esperado:
        falhas.append(f"dados falsos: sobrou {obtido - esperado}, faltou {esperado - obtido}")

    # 2- Casos com campos desconhecidos (None), como vêm do Adzuna.
    base = {"area": None, "cidade": "Goiânia", "modalidade": None, "linguagens": []}
    casos = [
        ("tudo desconhecido mantém", {"cidade": None}, True),
        ("Goiânia sem modalidade mantém", {}, True),
        ("Aparecida presencial mantém", {"cidade": "Aparecida de Goiânia", "modalidade": "presencial"}, True),
        ("São Paulo sem modalidade barra", {"cidade": "São Paulo"}, False),
        ("São Paulo híbrido barra", {"cidade": "São Paulo", "modalidade": "híbrido"}, False),
        ("São Paulo remoto mantém", {"cidade": "São Paulo", "modalidade": "remoto"}, True),
        ("só C# barra", {"linguagens": ["C#"]}, False),
        ("C# e Java mantém", {"linguagens": ["C#", "Java"]}, True),
        ("mobile barra", {"area": "mobile"}, False),
        ("sem sinal de TI barra", {"ti": False}, False),
        ("com sinal de TI mantém", {"ti": True}, True),
        ("dados só com Scala mantém", {"area": "dados", "linguagens": ["Scala"]}, True),
    ]
    for nome, mudancas, esperado_caso in casos:
        if passa_no_filtro({**base, **mudancas}) != esperado_caso:
            falhas.append(nome)

    print("ok" if not falhas else f"FALHOU: {falhas}")
