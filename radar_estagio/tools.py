
VAGAS_FALSAS = [
    {"id": 1, "titulo": "Estágio em Desenvolvimento Backend Python", "empresa": "Empresa Exemplo A",
     "cidade": "Goiânia", "modalidade": "híbrido", "area": "backend",
     "linguagens": ["Python"], "requisitos": ["FastAPI", "SQLAlchemy"],
     "ingles": "básico", "semestre_minimo": 2, "url": "https://exemplo.com/vaga-1"},  # filtro: passa

    {"id": 2, "titulo": "Estágio em Inteligência Artificial e NLP", "empresa": "Empresa Exemplo B",
     "cidade": "Remoto", "modalidade": "remoto", "area": "ia",
     "linguagens": ["Python"], "requisitos": ["NLP", "LLMs", "Hugging Face"],
     "ingles": "intermediário", "semestre_minimo": 2, "url": "https://exemplo.com/vaga-2"},  # passa

    {"id": 3, "titulo": "Estágio em Agentes de IA e Automação", "empresa": "Empresa Exemplo C",
     "cidade": "Goiânia", "modalidade": "presencial", "area": "ia",
     "linguagens": ["Python"], "requisitos": ["Google ADK", "APIs REST"],
     "ingles": "intermediário", "semestre_minimo": 1, "url": "https://exemplo.com/vaga-3"},  # passa

    {"id": 4, "titulo": "Estágio em Desenvolvimento Java", "empresa": "Empresa Exemplo D",
     "cidade": "Goiânia", "modalidade": "híbrido", "area": "backend",
     "linguagens": ["Java"], "requisitos": ["POO", "MySQL"],
     "ingles": "nenhum", "semestre_minimo": 2, "url": "https://exemplo.com/vaga-4"},  # passa

    {"id": 5, "titulo": "Estágio em Programação em C (Sistemas Embarcados)", "empresa": "Empresa Exemplo E",
     "cidade": "Anápolis", "modalidade": "presencial", "area": "embarcados",
     "linguagens": ["C"], "requisitos": ["Linux", "Git"],
     "ingles": "básico", "semestre_minimo": 2, "url": "https://exemplo.com/vaga-5"},  # BARRADA: presencial fora de Goiânia

    {"id": 6, "titulo": "Estágio em Dados e Automação", "empresa": "Empresa Exemplo F",
     "cidade": "Goiânia", "modalidade": "híbrido", "area": "dados",
     "linguagens": ["Python"], "requisitos": ["Pandas", "Power BI", "SQL"],
     "ingles": "básico", "semestre_minimo": 3, "url": "https://exemplo.com/vaga-6"},  # passa

    {"id": 7, "titulo": "Estágio em Desenvolvimento Full Stack", "empresa": "Empresa Exemplo G",
     "cidade": "Brasília", "modalidade": "híbrido", "area": "fullstack",
     "linguagens": ["Python"], "requisitos": ["React", "PostgreSQL", "Docker"],
     "ingles": "intermediário", "semestre_minimo": 3, "url": "https://exemplo.com/vaga-7"},  # BARRADA: híbrido fora de Goiânia

    {"id": 8, "titulo": "Estágio em Desenvolvimento Backend", "empresa": "Empresa Exemplo H",
     "cidade": "São Paulo", "modalidade": "presencial", "area": "backend",
     "linguagens": ["Python"], "requisitos": ["Django", "AWS"],
     "ingles": "intermediário", "semestre_minimo": 2, "url": "https://exemplo.com/vaga-8"},  # BARRADA: presencial fora de Goiânia

    {"id": 9, "titulo": "Estágio em Engenharia de Dados", "empresa": "Empresa Exemplo I",
     "cidade": "Remoto", "modalidade": "remoto", "area": "dados",
     "linguagens": ["Scala"], "requisitos": ["Spark", "Airflow", "Databricks"],
     "ingles": "avançado", "semestre_minimo": 5, "url": "https://exemplo.com/vaga-9"},  # passa (não-dev, remoto). Combina pouco com o perfil, mas isso é da fase 5

    {"id": 10, "titulo": "Estágio em Desenvolvimento .NET", "empresa": "Empresa Exemplo J",
     "cidade": "Curitiba", "modalidade": "presencial", "area": "backend",
     "linguagens": ["C#"], "requisitos": [".NET", "SQL Server", "Azure"],
     "ingles": "básico", "semestre_minimo": 3, "url": "https://exemplo.com/vaga-10"},  # BARRADA: local e linguagem

    {"id": 11, "titulo": "Estágio em Desenvolvimento Mobile", "empresa": "Empresa Exemplo K",
     "cidade": "Goiânia", "modalidade": "presencial", "area": "mobile",
     "linguagens": ["Dart"], "requisitos": ["Flutter", "Firebase"],
     "ingles": "básico", "semestre_minimo": 4, "url": "https://exemplo.com/vaga-11"},  # BARRADA: dev sem Java/Python/C

    {"id": 12, "titulo": "Estágio em DevOps e Infraestrutura", "empresa": "Empresa Exemplo L",
     "cidade": "Belo Horizonte", "modalidade": "híbrido", "area": "cloud_devops",
     "linguagens": [], "requisitos": ["Kubernetes", "Terraform", "Jenkins", "Linux"],
     "ingles": "intermediário", "semestre_minimo": 6, "url": "https://exemplo.com/vaga-12"},  # BARRADA: híbrido fora de Goiânia

    {"id": 13, "titulo": "Estágio em Ciência de Dados", "empresa": "Empresa Exemplo M",
     "cidade": "Remoto", "modalidade": "remoto", "area": "dados",
     "linguagens": ["R"], "requisitos": ["Estatística", "Machine Learning"],
     "ingles": "avançado", "semestre_minimo": 6, "url": "https://exemplo.com/vaga-13"},  # passa (não-dev, remoto)

    {"id": 14, "titulo": "Estágio em Manutenção de Computadores", "empresa": "Empresa Exemplo N",
     "cidade": "Goiânia", "modalidade": "presencial", "area": "suporte_hardware",
     "linguagens": [], "requisitos": ["Montagem de PCs", "Redes"],
     "ingles": "nenhum", "semestre_minimo": 1, "url": "https://exemplo.com/vaga-14"},  # BARRADA: área excluída

    {"id": 15, "titulo": "Estágio em Cloud e DevOps", "empresa": "Empresa Exemplo O",
     "cidade": "Goiânia", "modalidade": "híbrido", "area": "cloud_devops",
     "linguagens": [], "requisitos": ["Docker", "AWS", "Linux"],
     "ingles": "básico", "semestre_minimo": 3, "url": "https://exemplo.com/vaga-15"},  # passa. Pede Docker (lacuna!)

    {"id": 16, "titulo": "Estágio em Help Desk de Software", "empresa": "Empresa Exemplo P",
     "cidade": "Goiânia", "modalidade": "presencial", "area": "suporte_software",
     "linguagens": [], "requisitos": ["Atendimento", "SQL básico"],
     "ingles": "nenhum", "semestre_minimo": 1, "url": "https://exemplo.com/vaga-16"},  # passa

    {"id": 17, "titulo": "Estágio em Cibersegurança", "empresa": "Empresa Exemplo Q",
     "cidade": "Remoto", "modalidade": "remoto", "area": "ciberseguranca",
     "linguagens": ["Python"], "requisitos": ["Pentest", "Redes"],
     "ingles": "intermediário", "semestre_minimo": 4, "url": "https://exemplo.com/vaga-17"},  # BARRADA: área excluída (mesmo remoto e com Python)

    {"id": 18, "titulo": "Estágio em Desenvolvimento Front-end", "empresa": "Empresa Exemplo R",
     "cidade": "Remoto", "modalidade": "remoto", "area": "frontend",
     "linguagens": ["JavaScript"], "requisitos": ["React", "CSS"],
     "ingles": "básico", "semestre_minimo": 2, "url": "https://exemplo.com/vaga-18"},  # BARRADA: dev só JavaScript
]

def buscar_vagas(termos_de_busca: list[str] | None = None) -> dict:
    """
    Lista vagas de estágio de TI da base de vagas disponível, por tema.
    
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
    
    # Implementação da função de busca de vagas
    try:
        #protetor: se não houver termos de busca, devolve todas as vagas
        if not termos_de_busca:
            return {"numero_vagas": len(VAGAS_FALSAS), "vagas": VAGAS_FALSAS, "status": "success"}
        #protetor: se termos_de_busca não for uma lista, lança ValueError
        if not isinstance(termos_de_busca, list):
            raise ValueError("termos_de_busca deve ser uma lista de strings.")
        
        #preparação de termos: tudo minusculo e separar palavras como 'machine learning' em ['machine', 'learning']
        termos_em_palavras = [termo.lower().split() for termo in termos_de_busca]
        for vaga in VAGAS_FALSAS: # pega 1 vaga por vez
            
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
    