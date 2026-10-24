"""Busca no currículo por significado (RAG): quebra o perfil em chunks, guarda os embeddings no Chroma
e acha os chunks mais parecidos com um texto (por exemplo, o que uma vaga pede).

Os embeddings vêm do Gemini e gastam chamadas da API. Os dos chunks ficam no disco e só são refeitos
quando o texto do chunk muda. Só serve como evidência ("onde você usou isso"): as notas de similaridade
ficam espremidas (0,65 a 0,80), então não decidem nada sozinhas.
"""
import hashlib
from pathlib import Path

import chromadb
from google import genai
from google.genai import types

CAMINHO_INDICE = Path(__file__).parent / "chroma_db"
MODELO_EMBEDDING = "gemini-embedding-001"
CAMPOS_FORA_DO_INDICE = {"fonte", "objetivo", "formacao", "idiomas"}  # não são evidência de habilidade


def montar_chunks(perfil: dict) -> list[str]:
    """Quebra o perfil em textos que se entendem sozinhos: um por projeto, curso, grupo de habilidades etc."""
    chunks = []

    for campo, valor in perfil.items():
        if campo in CAMPOS_FORA_DO_INDICE:
            continue
        if isinstance(valor, str):
            chunks.append(f"{campo}: {valor}")
        elif isinstance(valor, list):
            for item in valor:
                if isinstance(item, dict):  # projeto
                    tecnologias = ", ".join(item["tecnologias"])
                    chunks.append(f"Projeto {item['nome']}. Tecnologias: {tecnologias}. {item['resumo']}")
                else:
                    chunks.append(f"{campo}: {item}")
        elif isinstance(valor, dict):
            for subcampo, subvalor in valor.items():
                if isinstance(subvalor, list):
                    subvalor = ", ".join(subvalor)
                chunks.append(f"{campo}.{subcampo}: {subvalor}")

    return chunks


def _gerar_embeddings(textos: list[str], tarefa: str) -> list[list[float]]:
    """Uma chamada ao Gemini. tarefa: "RETRIEVAL_DOCUMENT" (o que será procurado) ou "RETRIEVAL_QUERY" (o pedido)."""
    cliente = genai.Client()  # numa variável: sem referência, o cliente é fechado antes de a chamada sair
    resposta = cliente.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=textos,
        config=types.EmbedContentConfig(task_type=tarefa),
    )
    return [e.values for e in resposta.embeddings]


def _colecao():
    """Abre a coleção do currículo (e cria a pasta do índice na primeira vez). Fica aqui dentro para
    importar este arquivo não criar nada no disco."""
    banco = chromadb.PersistentClient(path=str(CAMINHO_INDICE))
    return banco.get_or_create_collection("curriculo", metadata={"hnsw:space": "cosine"})


def indexar_perfil(perfil: dict) -> dict:
    """Deixa o índice igual ao perfil: gera embedding só dos chunks novos e apaga os que saíram.
    O id do chunk é o hash do texto, então texto igual não é gerado de novo.
    Se mudar o modelo ou a tarefa do embedding, apague a pasta chroma_db: o texto não muda, o id também não,
    e os vetores velhos ficariam.

    Returns:
        {"novos": quantos foram gerados, "removidos": quantos saíram, "total": quantos há no índice}
    """
    chunks = list(dict.fromkeys(montar_chunks(perfil)))  # texto repetido daria id repetido, e o Chroma recusa
    colecao = _colecao()
    ids = [hashlib.sha1(c.encode()).hexdigest() for c in chunks]

    existentes = set(colecao.get(ids=ids)["ids"])
    novos = [(i, c) for i, c in zip(ids, chunks) if i not in existentes]
    if novos:
        colecao.add(
            ids=[i for i, _ in novos],
            documents=[c for _, c in novos],
            embeddings=_gerar_embeddings([c for _, c in novos], "RETRIEVAL_DOCUMENT"),
        )

    antigos = set(colecao.get()["ids"]) - set(ids)
    if antigos:
        colecao.delete(ids=list(antigos))

    return {"novos": len(novos), "removidos": len(antigos), "total": colecao.count()}


def buscar_evidencias(texto: str, quantos: int = 3) -> list[dict]:
    """Os chunks do currículo mais parecidos com o texto, do mais para o menos parecido.
    Uma chamada ao Gemini (o embedding do texto). Devolve [] se o índice estiver vazio.

    Returns:
        Lista de {"texto": o chunk, "similaridade": 0 a 1}.
    """
    colecao = _colecao()
    if colecao.count() == 0:
        return []
    vetor = _gerar_embeddings([texto], "RETRIEVAL_QUERY")[0]
    r = colecao.query(query_embeddings=[vetor], n_results=quantos)
    return [{"texto": doc, "similaridade": round(1 - d, 2)} for d, doc in zip(r["distances"][0], r["documents"][0])]
