# Vagas falsas só para testar o filtro (python -m radar_estagio.filtro). A busca real usa o Google Jobs (SerpApi).

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
