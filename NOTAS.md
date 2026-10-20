# Notas de aprendizado e decisões

Rascunho para virar a seção de decisões do README (fase 10).

## Perfil e análise de compatibilidade (17/10/2026, PR #1)

- **Perfil:** `radar_estagio/perfil.json`, feito a partir do `CV_Heitor_Cabral.pdf` (a pasta `curriculos/` é ignorada pelo
  Git). Só os campos úteis para a análise; sem telefone e e-mail. Django, NLP e LLMs ficam em `habilidades_parciais`
  (o agente diz "em estudo"). O perfil é pequeno e cabe inteiro no pedido, então **não precisa de RAG** agora.
- **Tool `carregar_perfil`:** lê o JSON e devolve. Erros previstos (arquivo faltando, JSON quebrado) viram mensagem fixa,
  no mesmo padrão da `buscar_vagas`.
- **Quem dá a nota:** o modelo, seguindo regras na `instruction` (nota 0-100, "Você já tem", "Lacunas", ordem decrescente).
  Não é cálculo no código, então a nota pode variar um pouco entre conversas. Peso: 70% tecnologias, 30% área e nível.
- **Teste à mão no `adk web` (7 perguntas) achou 4 problemas, e o que fiz:**
  1. A nota ignorava exigência eliminatória (Liferay pedia 6º período, Narwal pedia graduação concluída; ficaram com 80
     e 75). Regra nova: exigência que o usuário não cumpre limita a nota a 60 e mostra "Atenção:".
  2. O agente inventava habilidades ("visão geral de TI", "domina bancos de dados"). Regra nova: "Você já tem" só com itens
     escritos no perfil, sem adjetivos; se nada bate, escrever "Nenhuma correspondência direta".
  3. O agente reescreveu um título de vaga. Regra nova: copiar o título exatamente como veio.
  4. Suporte, help desk e vendas ficavam com 45-55. Regra nova: limite de 50.
  Depois das regras, Liferay caiu para 60 e Narwal para 55, ambas com "Atenção:".
- **Bug do filtro 1 (Auvo, vaga de vendas):** passou como "TI" porque a descrição listava "Ciência da Computação" entre os
  cursos aceitos. Nome de curso diz *quem pode se candidatar*, não o que o trabalho é. Tirei `ciencia da computacao`,
  `engenharia de software` e `engenharia da computacao` de `TERMOS_TI_DESCRICAO`. Testei nas 33 vagas salvas: só a Auvo saiu.
- **Bug do filtro 2 (Amazon Connect, sênior):** o Google Jobs marcou a vaga com a extensão "Estágio", mesmo pedindo "6+ years
  of experience". Campo novo `exige_experiencia` (`_exige_experiencia`): título com sênior/pleno/sr, ou 2 ou mais anos de
  experiência na descrição (português e inglês). **Falso positivo que eu mesmo causei:** "empresa com mais de 20 anos de
  experiência" (Clicksoft) barrou um estágio de verdade; passei a ignorar números em frases com "empresa", "somos", "temos"
  etc. Moral: testar a regra nova em todos os dados salvos e olhar *cada* vaga que ela barra, não só a que eu queria barrar.
- **Como depurei sem inventar causa:** quando não tinha o texto da vaga, disse que não sabia e gastei 1 busca (depois mais 2)
  para pegar o texto real, salvando em `dados_serpapi/` para reusar. Gasto total do dia: 5 buscas de 250.
- **Pausa de 0,5 s entre buscas (`PAUSA_ENTRE_BUSCAS`):** é só precaução contra *rate limiting* (muitos pedidos colados,
  erro HTTP 429). Nunca vi 429 aqui e não testei sem a pausa. Se um dia aparecer, o certo é *retry com backoff*.
- **RAG (ideia para depois):** o primeiro uso que faz sentido é busca por significado nas vagas salvas, quando o banco
  tiver centenas delas. Currículo e projetos não precisam.
- **Git (aprendizado):** reescrevi as mensagens de commits da branch (ainda não enviada) com `git filter-branch --msg-filter`
  para tirar uma linha `Co-Authored-By`. Só é seguro antes do `push`, porque muda o hash de todos os commits. Conferi com
  `git diff <backup> HEAD` que o conteúdo ficou idêntico, e só então apaguei a branch de backup.
- **Feito em 18/10/2026 (direto na `main`):** tirei o `print` `[funil]`; "auxiliar" e "aprendiz" no título agora barram
  a vaga (junto com pleno/sênior, em `_exige_experiencia`); `javascript` entrou nos termos de TI da descrição (`java`
  não casa com `javascript` porque a busca é por palavra inteira, então precisou de termo próprio).
- **Pendências:** calcular a nota em código (hoje o modelo dá a nota); salvar resultados em banco; conferir se a resposta do agente foi cortada na vaga 13 da pergunta 1
  (pode ter sido só a cópia); a vaga Strider foi barrada por experiência e eu não li o texto para confirmar.

## Nota calculada em código (fases 4 e 5, 19-20/10/2026)

- **Decisão final:** nota por **palavras-chave**, sem modelo e sem cache (`radar_estagio/nota.py`, ~80 linhas). A mesma
  vaga e o mesmo perfil dão sempre a mesma nota. É o mesmo estilo do `filtro.py`: função simples chamada dentro da
  `buscar_vagas`, que põe `compatibilidade` em cada vaga e ordena. A `instruction` só manda copiar.
- **Caminho que abandonei:** o Gemini lia a vaga (temperatura 0, formato
  fixo) e o código fazia a conta. Funcionou (23 vagas, 1 chamada, 31 s), mas exigiu cache por hash, schema, tratamento
  de erro e a sessão guardando as vagas: ~180 linhas para uma nota. Concluí que a complexidade não compensava agora.
  Achados: T=0 não garante o mesmo resultado (o que garantia era o cache); mudando o prompt, as extrações das mesmas
  23 vagas mudaram; vaga com 1 só requisito coberto tira nota alta. Se um dia a lista de palavras não bastar, o
  Gemini volta só como reserva para vagas em que ela não achou nada.
- **Fórmula:** 70% tecnologias (fração das tecnologias citadas que o perfil cobre; "em estudo" vale metade) + 30%
  área (backend/IA 1,0; dados e cloud/devops 0,6; área não detectada 0,5; título com suporte, help desk, atendimento,
  vendas ou redes 0). Tetos: exigência eliminatória (período maior que `periodo_atual` do perfil, graduação concluída)
  = 60; fora do objetivo = 50. Sem nenhuma tecnologia reconhecida, a parte das tecnologias vale 30% e a vaga sai
  marcada como "pouco confiável" (com 50%, vaga sem informação ficava acima de vaga com 1 de 2 requisitos).
- **De onde vêm as tecnologias da vaga:** linguagens do detector que já existia (`vaga["linguagens"]`) mais o dicionário
  `TECNOLOGIAS` (nome no perfil -> como a vaga escreve). "banco de dados" conta como SQL e "lógica de programação" como
  Python (decisão minha: muitas vagas de TI pedem só isso; efeito: "Estágio de TI" do Água Santa tira 85).
  **O que não está no dicionário não existe para a nota.** Para ampliar, é só acrescentar uma linha.
- **Período e graduação:** regex acha "5º período", "3º ao 6º período" e "semestre" na descrição; graduação concluída
  vem de "graduação concluída" na descrição ou "graduado" no título. `_sem_acento` transforma `º` em `o`, por isso o
  regex aceita um `o` depois do número.
- **Import circular:** `tools.py` chamava `nota.py` e `nota.py` importa helpers do `tools.py`. Resolvi importando
  `avaliar_vagas` dentro da `buscar_vagas`.
- **Teste (23 vagas salvas, sem API):** Liferay 60 com "Atenção: exige 6º período", Narwal com "Atenção: exige graduação
  concluída", Equatorial (só pede SQL) 88. Suporte técnico da ALM ficou em 50, o teto da regra.
- **Teste no `adk web` (20/10/2026, 19 vagas ao vivo) achou 4 erros, corrigidos:**
  1. "Postgre" (como a Narwal escreve) não casava com PostgreSQL: acrescentei o apelido.
  2. "SQL Server" contava como SQL e "Bancos de Dados Vetoriais" contava como "banco de dados" genérico (SQL): agora são
     tecnologias próprias (lacunas). O dicionário vai em ordem e o trecho já contado sai do texto (`re.sub`), então o
     nome mais específico vem antes do genérico.
  3. A resposta mostrava "Python" como se a vaga pedisse, mas ela dizia "lógica de programação": os genéricos agora
     aparecem como `python ("lógica de programação")` (dicionário `GENERICOS`).
  4. Vaga de suporte técnico com lacuna "machine learning": vinha de uma lista de cursos aceitos ("Superior cursando em
     ..., Inteligência Artificial e Machine Learning"). Mesmo erro do caso Auvo (nome de curso não é requisito). Agora o
     trecho depois de "cursando" é descartado quando tem 4 ou mais vírgulas (lista de cursos).
  Como achei o texto da vaga sem gastar busca: o `adk web` guarda tudo em `radar_estagio/.adk/session.db` (tabela
  `events`), inclusive a resposta completa das tools.
- **Em aberto:** vaga que pede 1 só tecnologia coberta tira nota muito alta (Equatorial 88, Neobag 85). A constante
  `MIN_TECNOLOGIAS` (hoje 2) divide as tecnologias por `max(citadas, MIN)`. Simulado nas 19 vagas: com 2, Equatorial 53 e
  Neobag 50; com 3, Equatorial 41, Neobag 38 e Água Santa 62. Escolhido: 2.
- **Falta:** reiniciar o `adk web` e testar de novo com o código corrigido.

## Fonte atual: Google Jobs via SerpApi (troca feita em 16/10/2026)

**As seções do Adzuna mais abaixo são histórico** (o código do Adzuna foi removido; está no commit `211a37e`).

- **Por que trocou:** o Adzuna devolvia ~10 vagas por busca. O diagnóstico com um `print` do funil mostrou que a API só tinha
  36 (Goiânia) e 22 (remotas) vagas para a busca; 46 das 58 eram de outras áreas, e o filtro as barrava (certo). O limite
  era a oferta de estágio de TI no Adzuna, não o código, a paginação ou o modelo. A cota gratuita (25 chamadas de teste, não
  diária) estava no fim.
- **Gupy foi testada e descartada:** a API pública do portal (`portal.gupy.io/api/job-search/jobs`) tem filtros `type` e
  `state`, mas há só 53 estágios em todo Goiás e quase nenhum de TI (nem lendo as descrições). Busca por `jobName` casa quase
  como frase ("estágio python" = 0). Também deu 0 para estágio remoto + "desenvolvedor". Os termos de uso não proíbem
  scraping de forma expressa, mas proíbem "agregar, copiar ou duplicar partes" da plataforma (zona cinzenta).
- **SerpApi (Google Jobs):** plano grátis de 250 buscas/mês. Cada página = 10 vagas = 1 busca. Em 5 buscas de teste vieram
  27 vagas únicas; 19 passam no filtro (14 em Goiânia/Aparecida, 5 remotas). Agrega Glassdoor, Indeed, Catho, LinkedIn etc.
- **Como a `buscar_vagas` funciona agora:** uma busca por termo (`"estágio <termo> Goiânia"`, no máximo 3) mais uma remota
  (`"estágio <tema> remoto"`) = até 4 buscas por pergunta (~60 perguntas/mês). Sem tema, termos padrão `TI`, `dados`,
  `programação` e tema remoto `desenvolvedor` (medidos). `"estágio python Goiânia"` retornou **0**: o Google Jobs não tolera
  termo muito específico. Por isso a `instruction` manda **não passar argumento** quando não há tema.
- **Conversão (`_converter_vaga_serpapi`):** remoto = extensão `Trabalho de casa` ou local `Qualquer lugar`; cidade = o que vem
  antes de `,` ou ` - `; link = primeiro `apply_options`. Campo novo `estagio` (extensão `Estágio` ou a palavra no título/
  descrição) e regra nova no filtro: sem sinal de estágio, barra (mantém o nível; evita "Auxiliar de TI").
- **Dedup:** a mesma vaga aparece com `job_id` diferente em sites diferentes, então a chave é título + empresa (sem acento).
- **Filtro de tipo `uds` do SerpApi não foi usado:** o código é gerado por busca, exigiria 2 buscas por pergunta.
- **Segurança:** erros da SerpApi/requests viram mensagens fixas (a URL traz a `api_key`). Chave só no `.env` (`SERPAPI_KEY`).
- **Erro meu a lembrar:** `printf >> .gitignore` em arquivo sem quebra de linha final cola a linha nova na última (`.adk/` +
  `dados_gupy/` viraram uma linha e desligaram as duas proteções). Conferir com `git check-ignore -v`.
- **Erro meu a lembrar:** `python -m radar_estagio.tools` roda o `__main__` e chama a API de verdade (gasta cota). Não rodar
  só para "ver se importa".
- **Fluxo de Git que usei (aprendizado):** criar a branch (`git switch -c`), commitar nela, testar, e só então
  `git switch main`, `git merge feat/fonte-serpapi`, `git push`. O push é o único passo que publica; o merge local dá para
  desfazer. `git branch -d` só apaga a branch se ela já estiver dentro da `main` (`-D` força e perde commits não mesclados;
  usei `-D` na branch da Gupy de propósito, o commit era `8df70b9`).
- **Fast-forward:** o merge foi *fast-forward* porque a `main` não recebeu commits novos enquanto a branch existia
  (`git merge-base main feat/fonte-serpapi` = a ponta da `main`). Ou seja, a história continuou em linha reta e o Git só
  moveu a `main` para a frente, sem commit de merge nem conflito. **Não tem a ver com o conteúdo** (ter removido código
  não influencia): se alguém commitasse na `main` no meio, o merge teria que juntar dois caminhos, mesmo se a branch só
  adicionasse linhas. `git merge --ff-only` recusa se não for possível, o que serve de trava de segurança.
- **Pendências novas:** filtrar vagas de áreas fora do foco por título (ex.: "Auxiliar", "Aprendiz"); decidir se
  `JavaScript` entra nos termos de TI do detector; análise com currículo (fases 4 e 5) para ordenar o que sobrar.

## try/except: cuidado com `except Exception` em código meu

**O que aconteceu (fase 1):** troquei `VAGAS_FALSAS` por `VAGAS_FALSOS` (typo) dentro do `try` de `buscar_vagas`.
O Python não mostrou erro nenhum. A função devolveu `"status": "error"` com a mensagem
`name 'VAGAS_FALSOS' is not defined`, e o programa seguiu em frente.

**Por que importa:** um erro *meu* (bug) ficou disfarçado de erro *de execução*. Dentro do agente,
o modelo só leria a mensagem e diria ao usuário "tive um problema", sem eu ver o stack trace no terminal.

**Regra:**
- `except Exception` largo, em volta de código meu, esconde bugs.
- `try/except` serve para falhas **externas e imprevisíveis** (rede, API fora do ar, resposta fora do formato).
- Na fase 2, colocar dentro do `try` só a chamada externa e capturar exceções específicas, não `Exception`.

**Convenção do retorno das tools (doc do ADK, página function tools):**
- Retornar dicionário com `"status"`.
- Mensagem de erro legível em `"error_message"` (não código numérico).
- "Não achou nenhuma vaga" é `"success"` com 0 resultados, não erro.

## Decisões da `buscar_vagas` (fase 1)

- Um parâmetro: `termos_de_busca: list[str] | None = None` (modelo manda termos + sinônimos).
- Sem termos (`None` ou `[]`): devolve todas as vagas. Texto no lugar de lista: erro com mensagem clara.
- Procura em `titulo`, `area`, `linguagens` e `requisitos`, juntos numa lista única de palavras em minúsculas.
- Palavra inteira (não pedaço): "ia" não pode casar com "Ciência" nem "Engenharia".
- Termo de várias palavras: todas as palavras do termo precisam estar na vaga. Entre termos: basta um.
- Currículo e regras de filtro NÃO entram aqui (funil: buscar larga, filtrar com regras, analisar com currículo).
- Algoritmo: busca linear, suficiente nesta escala. Índice invertido seria a melhoria se um dia precisar.

## Bugs achados e resolvidos (fase 1)

Os dois eram do mesmo trecho (o laço de palavras dentro do laço de termos):

1. **"Alguma palavra" em vez de "todas":** `["java backend"]` trazia vagas sem Java, `["sql server"]` trazia vagas só com "SQL".
   Causa: o `if` decidia a cada palavra, sem lembrar se uma anterior tinha falhado.
   Correção: `termo_casou` começa `True` e vira `False` se faltar alguma palavra; o `if termo_casou` fica
   **fora** do laço de palavras (se ficar dentro, decide cedo demais e o resultado depende da ordem das palavras).
2. **Duplicatas:** `["backend", "python"]` devolvia as vagas 1 e 8 duas vezes.
   Causa: o `append` rodava uma vez por termo que casava. Correção: `append` + `break` quando um termo casa,
   saindo do laço de termos.

Lição: rastrear o código à mão (tabela de passos com os valores reais) acha esse tipo de bug mais rápido que adivinhar.

Testes que passaram: `["java backend"]` → [4]; `["backend java"]` → [4]; `["sql server"]` → [10];
`["python"]` → 1, 2, 3, 6, 7, 8, 17; `["IA"]` → 2, 3; `[]` e `None` → 18; texto no lugar de lista → error;
termos de cibersegurança (com e sem acento) → vaga 17.

## Limitações conhecidas

- Acentos contam: "Cibersegurança" não casa com "ciberseguranca". Por enquanto o modelo manda as duas grafias;
  melhoria possível: normalizar acentos dentro da função.
- "back-end" não casa com "backend".
- O `except Exception` largo esconde bugs (ver seção de try/except). Revisar na fase 2.

## Status

- **Fase 1: concluída e publicada.** `buscar_vagas` com 18 vagas falsas, ligada ao agente e testada no `adk web`.
  `.env` fora do Git. Repo no GitHub ligado (`origin/main`). Commits da fase:
  `e890987` (estrutura), `5bf2c6c` (`buscar_vagas`), `0262341` (agente + testes no `adk web`).
- **Fase 2: concluída e publicada (16/10/2026).** Começou com o Adzuna (`b8e3d02..de4f726`), mas a fonte final é o
  **Google Jobs via SerpApi** (ver a seção no topo). `buscar_vagas` busca, converte, filtra (TI, estágio, cidade, área,
  linguagem) e foi testada no `adk web`. Está na `main` do GitHub (`cd4459e`). Commits da troca: `63b17de` (SerpApi),
  `4bd18ab` (`.gitignore`), `cd4459e` (remove o Adzuna, atualiza as notas). O código do Adzuna está em `211a37e`.
- **Fases 4 e 5: em andamento.** Feito: `perfil.json`, `carregar_perfil` e a análise de compatibilidade na instruction
  (nota, "Você já tem", lacunas), mesclados na `main` pelo PR #1 (`ac761a7`). Nota calculada em código por palavras-chave (20/10/2026); falta testar no `adk web`.
- **Fase 10, parte 1: feita (19/10/2026).** README publicado (`72651f4`) com banner (`docs/banner.svg`), badges,
  diagramas Mermaid e `.env.example`; aviso de "em desenvolvimento" no topo.
- **Fase 10, parte 2: no fim do projeto.** Atualizar o README com o estado final (tirar o aviso de desenvolvimento,
  roadmap, exemplo real de resposta no lugar do ilustrativo, seção de decisões a partir deste `NOTAS.md`).
- **Próximo:** terminar as fases 4 e 5 (nota em código). Fases 3, 6, 7 e 8 ainda não estão descritas aqui.

## Escolha da API (fase 2, 14-15/10/2026)

- **Adzuna** cobre o Brasil (`/jobs/br/search/1`, resposta 200, `count` de 32271 para "estágio"). Pede `app_id` e
  `app_key` na query string. **Remotive** só tem vagas remotas, sem filtro de país nem de estágio, e limita a 4
  chamadas por dia: fica como complemento, se um dia precisar.
- **Plano gratuito do Adzuna = 25 chamadas de teste** ("Pending Activation"). Uso contínuo custa £8/mês (5.000
  chamadas/mês, 500/dia). Decisão: **não pagar agora.** Usei 5 das 25 chamadas (1 no navegador, 4 por script).
- **Plano B para o uso contínuo** (ainda não pesquisado): Jooble (chave gratuita por formulário) e o portal público da
  Gupy (API sem documentação oficial, precisa verificar os termos antes).
- **Regra:** desenvolver contra respostas **salvas em arquivo**, e chamar a API de verdade só no teste final.
- Cadastro: o formulário é para empresas, preenchi como projeto pessoal. As chaves nunca vão no chat nem no Git.
  Uma vez colei as chaves no chat; risco baixo (só 25 chamadas de teste), mas gerar chave nova se quiser.
- **A doc do Adzuna não diz** a lista de países nem os limites do plano gratuito; descobri testando.

## O que o Adzuna entrega (e o que não entrega)

- **Vem:** `title`, `description` (texto **cortado** com "…"), `company.display_name` (às vezes ausente),
  `location.display_name` ("Goiânia, Goiás", às vezes só "Brasil"), `created`, `redirect_url`, `category`.
- **Não vem:** área, linguagens, requisitos, modalidade, inglês, semestre. Por isso `ingles` e `semestre_minimo`
  saíram do formato interno, e `requisitos` virou `descricao`.
- **`category` não é confiável:** vagas de desenvolvimento vieram como `unknown`, `creative-design-jobs` e
  `other-general-jobs`. Não usar para filtrar.
- **Busca por "estágio" traz todas as áreas** (direito, contabilidade, farmácia). Em Goiânia (`where=Goiânia`,
  `distance=30`): 342 vagas de estágio, só cerca de 9 de TI. `what_or` com termos curtos ("ti", "dados") traz ruído.
- **Parâmetros usados:** `what`, `what_or`, `where`, `distance`, `results_per_page`. Nome de parâmetro errado não dá
  erro: o Adzuna ignora e devolve vagas do país inteiro. Conferir `count` e a cidade nos testes.
- **Muitos estágios não dizem "estágio" no título**, só na descrição. Por isso a regra de TI olha título e descrição.

## `_chamar_adzuna` (`tools.py`)

- **O `try/except` cobre só a chamada externa** e captura só `Timeout`, `ConnectionError`, `HTTPError` e `ValueError`
  (JSON inválido). Resolve a lição da fase 1 (`except Exception` esconde bugs).
- **Mensagens de erro fixas:** o texto de uma exceção do `requests` traz a URL com a `app_key`, e a mensagem de erro
  chega ao modelo. Por isso nunca usar `str(e)` aqui.
- **`requests.get(url, params=..., timeout=15)`:** `params` monta a query string e codifica os acentos; `timeout` evita
  esperar para sempre; `raise_for_status()` transforma 4xx/5xx em `HTTPError` (sem ele, um JSON de erro passaria
  por "zero vagas").
- **Chaves:** `os.environ.get` (o `adk web` carrega o `.env`). Fora do ADK, usar `load_dotenv` antes.

## Conversão e detectores (`tools.py`)

- **Formato interno:** `id`, `titulo`, `empresa` (pode ser `None`), `cidade` (`None` se "Brasil"), `modalidade`,
  `area`, `ti`, `linguagens`, `descricao`, `url`. O que não dá para saber vira `None`.
- **Por que palavras-chave e não modelo ou categoria:** grátis, instantâneo, testável e sem gastar o saldo do Gemini.
  A categoria do Adzuna é ruim. Limite: lista fixa, o que não está nela passa sem detectar. Melhoria futura: usar o
  modelo só nas vagas que sobrarem do filtro.
- **Área: só pelo título** (a descrição tem muito texto solto, como "app mobile" numa vaga de backend). **Linguagem:
  título e descrição.** Modalidade: "híbrido" é checado antes de "remoto", porque vagas híbridas citam os dois.
- **`_sem_acento`:** `normalize("NFKD")` separa a letra do acento, `encode("ascii", "ignore")` descarta o acento,
  `decode()` volta para texto, `lower()`. Resolve a limitação de acentos para os detectores (não para a busca por
  termos antiga).
- **Regex de palavra inteira:** `\b` + `re.escape(palavra)` + `\b`. `\b` é a fronteira entre letra/número/`_` e o resto.
  `re.escape` trata `+`, `.` como texto.
- **Regex de linguagens:** `(?<![\w+#])Nome(?![\w+#])` = "sem letra, número, `+` ou `#` colado antes ou depois".
  Não dá para usar `\b` porque `+` e `#` não são letras. Impede "Java" dentro de "JavaScript" e "C" dentro de
  "C++"/"C#". O "C" sozinho só vale **maiúsculo** (senão casaria "plano c"). Limite: "Ponto C" ainda casa.
- **Termos de TI:** título aceita termos curtos (ti, software, dados, desenvolvedor...); descrição só termos
  específicos (programação, Python, Java, SQL, "tecnologia da informação"...), porque descrições de outras áreas
  citam "sistemas" e "dados" à toa. Resultado nas respostas salvas: Goiânia passa de 20 para 9 vagas, todas de TI.
  Limite: "Estágio Graduação" sem nada de TI na descrição é barrado (não dá para saber).

## Filtro v2 (`filtro.py`, substitui as regras da seção acima)

- **Princípio:** só barra com certeza. Campo `None` mantém a vaga. A análise com o currículo (fases 4 e 5) decide o resto.
- **Regras:** (1) área excluída (mobile, frontend, cibersegurança, suporte de hardware) detectada pelo título;
  (2) `ti` é `False`; (3) cidade conhecida, fora de `CIDADES_BASE` e não remota. **Aparecida de Goiânia conta como
  base, e só ela** (limite do raio de 30 km); (4) a vaga cita linguagens e nenhuma é Java, Python ou C
  (ex.: só C#), nas áreas de programação e na área desconhecida (dados e cloud não exigem linguagem).
- **Decisão que mudou o combinado:** cidade fora da base com modalidade desconhecida **barra** (antes: mantinha).
  Sem isso, a busca nacional traria quase só vagas de São Paulo. Se incomodar, é só uma condição no `if`.
- **`ti` com `.get`:** os dados falsos antigos não têm o campo; sem ele, mantém.
- **Teste:** `python -m radar_estagio.filtro` roda os dados falsos (mesmo resultado de antes) e 12 casos com `None`.
  Nas respostas reais salvas: Goiânia 9 de 20 passam; nacional 3 de 20 (as de cidade desconhecida ou remoto).
- **Cuidado:** a busca nacional sem `where` desperdiça cota (a maioria é barrada). Para as remotas, melhor buscar
  com termo de remoto ou só olhar o que sobra depois do filtro.

## `buscar_vagas` com o Adzuna (15/10/2026)

- **Fluxo:** valida a entrada (`termos_de_busca is not None and not isinstance(..., list)` -> erro) -> `base` com
  `what="estágio"`, `results_per_page=50` e `what_or` = termos separados por espaço -> **duas buscas**: a 1 com
  `BUSCA_GOIANIA` (`where=Goiânia`, `distance=30`) e a 2 com `what="estágio remoto"` sem local -> junta sem repetir
  pelo `id` -> `_converter_vaga` -> `filtrar_vagas`. Se as duas buscas falham, devolve erro; se só uma falha, usa a outra
  (sem avisar da falha parcial).
- **Por que duas buscas:** o Adzuna não tem filtro "cidade OU remoto". Custo: 2 chamadas por pergunta.
- **`por_id.setdefault(vaga["id"], vaga)`:** guarda a vaga só se o `id` ainda não existe; a mesma vaga vinda das duas
  buscas entra uma vez. O `id` é a chave porque identifica a vaga de forma única (título e empresa podem repetir).
- **`is not None`:** é uma proposição (dá `True` ou `False`), "não é None". `None` = "ninguém passou nada", e é diferente
  de `[]` (lista vazia, que existe). Na validação, `None` precisa passar (busca sem tema é válida); mais abaixo,
  `if termos_de_busca:` trata `None` e `[]` igual.
- **O agente não "sabe" que sou de Goiânia:** quem decide é o código (`BUSCA_GOIANIA` e `CIDADES_BASE`) e a docstring,
  que o ADK manda ao modelo. A cidade é fixa; pedir "vagas em São Paulo" não acha nada.
- **Link:** o `url` é o `redirect_url` do Adzuna (página da vaga no site deles, com o `app_id` no `utm_source`). Meu
  `print` de teste não mostrava o link; corrigido.

### Diagnóstico: só 3 vagas no teste real

- Com `what_or="python java desenvolvedor"` a **própria API** devolveu só 3 vagas em Goiânia e 5 nas remotas. O filtro
  não era o problema: das 8, passaram 3 (barradas: sem sinal de TI, área excluída, cidade fora e não remota).
- **Causa:** a busca é restrita demais (`what="estágio"` E `what_or`, e "estágio remoto" exige as duas palavras).
  Sem termos, a API traz só 50 vagas de todas as áreas, e poucas são de TI. Respostas salvas fora do projeto.
- **Teste no `adk web` sem tema:** 10 vagas (4 em Goiânia, 6 remotas). Três eram duvidosas como TI (Melhoria
  contínua, CRO, Planejamento): passaram pela regra de TI por "tecnologia" e "dados". A análise com o currículo
  (fases 4 e 5) deve tratar isso.
- **Correção em aberto:** lista padrão de termos de TI quando o usuário não dá tema, ou buscar mais páginas.

### Caso "vagas de astronauta" (corrigido)

- **Problema:** devolveu o estágio de Java da Touch Health, e o agente escreveu "encontrei 1 vaga com os termos
  pesquisados", o que parecia dizer que a vaga tinha a ver com astronauta. A vaga entrou por um termo extra que o
  modelo acrescentou à lista: a busca é OR e a API também procura na descrição.
- **Causa provável:** a `instruction` mandava a "nova busca com termos mais amplos" e a docstring mandava incluir
  "termos relacionados", então o modelo derrapou para termos genéricos de TI.
- **Correção (só texto, sem lógica):** docstring pede só sinônimos diretos (máx. 5), proíbe termos genéricos de TI
  (software, tecnologia, desenvolvimento, engenharia, TI) e dá o caso "tema fora de TI"; `instruction` ganhou a seção
  "Confira se as vagas têm relação com o tema pedido" (separar "outras vagas de TI" e não dizer que correspondem) e a
  nova busca passa a ser com sinônimos do mesmo tema. **Testado no `adk web`: funcionou** (15/10/2026).
- **Lição:** texto de `instruction` e docstring molda os argumentos que o modelo manda. Uma instrução vaga como
  "termos mais amplos" gera ruído; e a resposta precisa dizer a verdade sobre o que casou.

## Python que revisei

- **`{**a, **b}`** junta dicionários em um novo (a chave do último vence); `a | b` faz o mesmo. Cópia rasa.
- **`any(cond for x in lista)`** é um `for` com `if` e `break`; `all` é o par. Dentro dos parênteses é uma expressão
  geradora (sem colchetes, calcula sob demanda).
- **`_nome`:** convenção para "uso interno do arquivo". O ADK só registra o que está em `tools=[...]`, então
  `_chamar_adzuna` e os detectores não aparecem para o modelo. `from x import *` não importa nomes com `_`.

## Filtro de regras v1 (fase 2, substituído pelo filtro v2 acima; fica como histórico)

- **Dois filtros em sequência, dentro de `buscar_vagas`:** primeiro `filtrar_vagas` (minhas regras fixas, não depende
  do pedido), depois a busca por termos (o tema do pedido atual). Os dois só removem vagas, então a ordem não muda o
  resultado; filtrar antes só evita comparar termos com vagas que seriam descartadas.
- **Regras:** área excluída (`suporte_hardware`, `ciberseguranca`, `frontend`, `mobile`); híbrido/presencial só em
  Goiânia (remoto vale de qualquer cidade); áreas de programação (`AREAS_DEV`: backend, fullstack, embarcados, ia)
  exigem Java, Python ou C. Áreas como dados, cloud e suporte de software não exigem linguagem.
- **Frontend e mobile ficam de fora por falta de interesse.** Tirar a área de `AREAS_DEV` NÃO barra a vaga: só deixa
  de checar a linguagem, e a vaga passa direto. Para barrar, a área vai em `AREAS_EXCLUIDAS`.
- **`if not linguagens & LINGUAGENS_ACEITAS`:** `&` entre conjuntos é a interseção (o que os dois têm em comum);
  o `&` é calculado antes do `not`, então é `not (linguagens & LINGUAGENS_ACEITAS)`: entra no `if` quando a
  interseção está vazia, ou seja, a vaga não tem nenhuma linguagem aceita. `and` seria outra coisa (junta duas
  condições, não compara os conjuntos).
- **Teste:** `python -m radar_estagio.filtro` imprime `ok` se os ids que passam são {1, 2, 3, 4, 6, 9, 13, 15, 16}.
  `tools.py` agora usa import relativo, então rodar `python radar_estagio/tools.py` direto não funciona mais;
  usar `python -m radar_estagio.tools`.
- **Limitação:** o filtro é fixo. Se o usuário pedir uma cidade fora de Goiânia, o agente não acha nada, porque essas
  vagas já foram removidas antes da busca. Aceitável para um único usuário com regras fixas.

## `agent.py`: o que aprendi

- **`description` x `instruction`** (doc do ADK): `description` é lida por *outros agentes* para decidir se encaminham
  uma tarefa (importa na fase 9); `instruction` é lida pelo *próprio agente* e define o comportamento.
- **Import:** dentro do pacote usa-se import relativo (`from .tools import buscar_vagas`).
  `from tools import ...` dá `ModuleNotFoundError`, porque o `adk web` carrega `radar_estagio` como pacote.
- **`tools=[buscar_vagas]`** recebe a função sem parênteses (referência, não chamada).
- **A `instruction` não pode contradizer o projeto.** A primeira versão mandava o agente interrogar o usuário antes de
  buscar e só usar a tool com "habilidades e experiências". Isso quebraria o teste do briefing, e quem conhece o perfil é
  o currículo (fases 4 e 5), não uma conversa. Faltava também a regra "nunca envia candidatura".
- A versão final diz: busca direto, usa interesses (backend, IA, dados) quando não há tema, nunca inventa vagas,
  não avalia compatibilidade ainda, tenta uma nova busca se vier vazio.

## Faturamento da API Gemini (decisões de segurança)

- Conta pré-paga: gasto sai do saldo (R$ 30). Sem saldo, as chamadas falham (erro 402); não continua cobrando.
- Recarga automática desativada. Teto de R$ 20/mês no projeto "Estagio agent" (experimental, pode passar um pouco
  por causa de ~10 min de latência na cobrança).
- Créditos não são reembolsáveis e expiram em 12 meses. Fechar a conta de faturamento perde o saldo.
- Não ativar outros serviços do Google Cloud nessa conta de faturamento (cobrariam no cartão por fora do saldo).
- Chave só no `.env` (ignorado). Se vazar, revogar e criar outra.

## Pendências

- [x] Fase 1: commit e push final (`0262341`, `.gitignore` com `.adk/`, `NOTAS.md`, `agent.py`).
- [x] Conferir o caso "vaga de astronauta": devolvia vaga de Java; corrigido na docstring e na `instruction`.
- [x] Trocar o exemplo da docstring de `buscar_vagas` por um tema menos "copiável" (agora "ciência de dados").
- [x] Fase 2: ler a documentação das APIs de vagas (Adzuna, Remotive) e confirmar se cobrem estágio no Brasil.
- [x] Fase 2: ligar `buscar_vagas` ao Adzuna (duas buscas, junção por `id`, conversão, filtro, docstring nova).
  O import de `dados_falsos` saiu do `tools.py`; o arquivo fica só para o teste do `filtro.py`.
- [x] Fase 2: a busca por termos local foi removida; os termos vão para o `what_or` da API.
- [x] Fase 2: lista padrão `TERMOS_BUSCA_PADRAO` quando não há tema (feita). Teste no `adk web` (15/10/2026,
  "me mostra vagas de estagio"): **10 vagas, as mesmas de antes** (4 em Goiânia, 6 remotas, com CRO, Planejamento e
  Melhoria contínua). Não melhorou: ou o `adk web` não recarregou o código, ou o gargalo é outro. Conferir o `what_or`
  enviado e, se for isso, tentar as páginas 2 e 3.
  **Cuidado:** `python -m radar_estagio.tools` chama o Adzuna de verdade (2 chamadas por execução).
- [ ] (antigo) Fase 2: trazer mais vagas: lista padrão de termos de TI quando não há tema, ou páginas 2 e 3. Testar com poucas
  chamadas (cota de teste: pelas minhas contas já passa de 20 das 25; conferir o número exato no painel do Adzuna).
- [ ] Fase 2: se só uma das duas buscas falhar, avisar na resposta (hoje usa a outra em silêncio).
- [ ] Fase 2: escolher a fonte para o uso contínuo (Jooble, Gupy ou pagar o Adzuna); pesquisar a doc antes.
- [x] Fase 2: testar no `adk web` com o Adzuna (sem tema e "astronauta").
- [ ] Opcional: modelo classificando só as vagas que sobraram do filtro, no lugar de palavras-chave.
- [x] Fase 2: filtro (`filtro.py`) validado contra os dados falsos e ligado dentro de `buscar_vagas`.
- [x] Fase 2: testar o filtro no `adk web` (14/10/2026, resultados na seção "Teste no `adk web` (fase 2)").
- [x] Orientar o modelo (docstring e `instruction`) a usar sinônimos diretos do tema, sem termos genéricos de TI.
- [x] Fase 2: restringir o `try/except` só à chamada externa e capturar exceções específicas (`_chamar_adzuna`).
  O `except Exception` antigo saiu junto com a busca local.
- [ ] Fase 4: decidir como usar os dois currículos (IA e dev): comparar com os dois ou unificar.
- [ ] Ideia: `require_confirmation` do ADK (experimental) se algum dia houver uma tool que aja no mundo.
- [ ] Ideia: normalizar acentos na busca, para não depender de o modelo mandar as duas grafias.

## Teste no `adk web` (fase 1, 13/10/2026)

- Pergunta sobre vagas de backend: o agente chamou `buscar_vagas(["backend","Python","Java","API"])` e listou as vagas
  com empresa, cidade, modalidade, tecnologias e link, sem inventar nada.
- Pergunta fora do assunto ("o que é um agente de IA?"): respondeu normalmente.
- Pergunta sem resultado ("vaga de astronauta"): disse que nenhuma vaga combina com o termo e sugeriu temas.
- **Aprendizado:** os termos que o modelo mandou são idênticos ao exemplo da docstring
  (`"backend" -> ["backend", "Python", "Java", "API"]`). Exemplos em docstring ancoram os argumentos do modelo.
  Se isso incomodar, trocar o exemplo por um tema diferente dos que o usuário costuma pedir.
- Apareceram vagas que o filtro da fase 2 vai barrar (.NET em Curitiba, presencial em São Paulo, cibersegurança).
  Isso era esperado: é o que a fase 2 resolve.
- Erro 503 ("high demand") do modelo apareceu uma vez: problema temporário do lado do Google, não do código.
- Faturamento: conta pré-paga com R$ 30 de saldo, recarga automática desativada, teto de R$ 20/mês no projeto.

## Teste no `adk web` (fase 2, filtro ligado)

Nenhuma vaga barrada pelo filtro apareceu em nenhum teste (5, 7, 8, 10, 11, 12, 14, 17 e 18 ficaram de fora).

- **"vagas de python":** o modelo mandou `["Python","backend","Django",...]` e voltaram as vagas 1, 2, 3, 4 e 6.
  A vaga 4 (Java) entra porque a área dela é `backend` e "backend" estava nos termos. Não é bug: o filtro de regras
  está certo (Java é aceito) e a busca por termos casou com um termo que o modelo acrescentou.
- **"cibersegurança":** primeira busca vazia; o agente fez a segunda busca mais ampla que a `instruction` pede
  (redes, infraestrutura) e achou a vaga 15 (Cloud e DevOps). A vaga 17 não apareceu.
- **"São Paulo":** a busca por termos não olha a cidade (só título, área, linguagens e requisitos), então o agente
  trouxe vagas de backend/Python. Ele disse que não havia vaga em São Paulo "na base", o que é meio enganoso: a
  vaga 8 existe, mas o filtro já a tinha removido.
- **"front-end":** nenhuma vaga, depois de duas buscas. Vaga 18 barrada.
- **"todas as vagas":** `buscar_vagas()` sem termos, 9 vagas (1, 2, 3, 4, 6, 9, 13, 15, 16), com a contagem dita antes.
- **"vagas de dados":** vieram 6, 9, 13 e também a 16 (Help Desk), porque o modelo mandou "SQL" e a vaga 16 tem
  "SQL básico" nos requisitos.

**Aprendizado:** o modelo amplia o tema com sinônimos e termos de áreas vizinhas, e basta um termo casar para a vaga
entrar. Isso é "busca larga" do funil; a análise com o currículo (fases 4 e 5) é quem vai ordenar e descartar o que
não combina. Se incomodar antes disso: pedir na docstring e na `instruction` que use só sinônimos do próprio tema.
