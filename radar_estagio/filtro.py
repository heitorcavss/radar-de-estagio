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

    # Nível: só estágio. Sem sinal de estágio no título, extensões ou descrição, barra.
    # .get pelo mesmo motivo do "ti": sem o campo, mantém.
    if vaga.get("estagio") is False:
        return False

    # Pede anos de experiência ou é vaga pleno/sênior: não é para estágio, mesmo que o Google
    # Jobs marque "Estágio". .get pelo mesmo motivo do "ti".
    if vaga.get("exige_experiencia") is True:
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



