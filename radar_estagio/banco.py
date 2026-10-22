from datetime import datetime
from pathlib import Path
from sqlalchemy import JSON, Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

CAMINHO_BANCO = Path(__file__).parent / 'radar_estagio.db' #Path(__file__).parent / 'radar_estagio.db') é o caminho do banco de dados SQLite que será criado no mesmo diretório do arquivo banco.py. O operador / é usado para concatenar o caminho do diretório com o nome do arquivo do banco de dados.

Base = declarative_base()
engine = create_engine(f'sqlite:///{CAMINHO_BANCO}')
Session = sessionmaker(bind=engine)

class Vaga(Base):
    __tablename__ = 'vagas'

    chave = Column(String, primary_key=True)  # título + empresa, sem acento e minúsculo: a mesma vaga não entra duas vezes
    titulo = Column(String, nullable=False)
    empresa = Column(String)
    cidade = Column(String)
    modalidade = Column(String)
    area = Column(String)
    linguagens = Column(JSON)
    descricao = Column(String)
    url = Column(String)
    primeira_vez_em = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)


def _chave(vaga: dict) -> str:
    """
    Gera a chave única para uma vaga com base no título e na empresa.
    A chave é formada pelo título e pela empresa, sem acentos e em minúsculas.
    """
    from .tools import _sem_acento
    
    titulo = _sem_acento(vaga.get('titulo') or '')
    empresa = _sem_acento(vaga.get('empresa') or '')
    return f"{titulo}_{empresa}"


def salvar_vagas(vagas: list[dict]) -> int:
    """
    Salva no banco as vagas que ainda não estão lá e devolve quantas eram novas.
    Se a vaga já existir (mesma chave), não é adicionada novamente.
    """
    novas = 0
    with Session() as session:
        for vaga in vagas:
            chave = _chave(vaga)
            if session.get(Vaga, chave) is None:
                nova_vaga = Vaga(
                    chave=chave,
                    titulo=vaga.get('titulo'),
                    empresa=vaga.get('empresa'),
                    cidade=vaga.get('cidade'),
                    modalidade=vaga.get('modalidade'),
                    area=vaga.get('area'),
                    linguagens=vaga.get('linguagens'),
                    descricao=vaga.get('descricao'),
                    url=vaga.get('url')
                )
                session.add(nova_vaga)
                session.commit()
                novas += 1
    return novas