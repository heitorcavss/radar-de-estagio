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