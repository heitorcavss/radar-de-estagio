CIDADE_BASE = "Goiânia"
AREAS_EXCLUIDAS = {"suporte_hardware", "ciberseguranca", "frontend", "mobile"}
# Áreas em que o estágio é de programação: exigem Java, Python ou C.
AREAS_DEV = {"backend", "fullstack", "embarcados", "ia"}
LINGUAGENS_ACEITAS = {"java", "python", "c"}


def passa_no_filtro(vaga: dict) -> bool:
    """Regras eliminatórias: devolve True se a vaga pode seguir para a análise."""
    if vaga["area"] in AREAS_EXCLUIDAS:
        return False

    # Remoto vale de qualquer cidade; híbrido e presencial só em Goiânia.
    if vaga["modalidade"] != "remoto" and vaga["cidade"] != CIDADE_BASE:
        return False

    if vaga["area"] in AREAS_DEV:
        linguagens = {l.lower() for l in vaga["linguagens"]}
        if not linguagens & LINGUAGENS_ACEITAS: # não (linguagens & LINGUAGENS_ACEITAS), se vazio, entra no if. & = interseção
            return False

    return True


def filtrar_vagas(vagas: list[dict]) -> list[dict]:
    return [v for v in vagas if passa_no_filtro(v)]


if __name__ == "__main__":
    from .dados_falsos import VAGAS_FALSAS

    esperado = {1, 2, 3, 4, 6, 9, 13, 15, 16}  # vagas sem "BARRADA" nos comentários de tools.py
    obtido = {v["id"] for v in filtrar_vagas(VAGAS_FALSAS)}
    print("ok" if obtido == esperado else f"FALHOU: sobrou {obtido - esperado}, faltou {esperado - obtido}")