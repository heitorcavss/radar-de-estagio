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
  tiver centenas delas. Currículo e projetos não precisam. (Em 24/10/2026 o RAG no currículo foi feito mesmo assim, como
  evidência ao lado da nota, e também para aprender: ver "RAG no currículo (fase 4)". O RAG nas vagas salvas segue em aberto.)
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
  área (backend/IA 1,0; dados e cloud/devops 0,6; área não detectada 0,5; título com suporte, help desk, atendimento
  ou vendas 0; "redes" não é mais penalizada desde 22/10, pois costuma ser complemento em dev). Tetos: exigência eliminatória (período maior que `periodo_atual` do perfil, graduação concluída)
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
- **22/10/2026: tecnologias com peso.** Python vale 3; FastAPI, LLMs e SQL valem 2; o resto vale 1 (`PESOS` em `nota.py`).
  A parte das tecnologias passou a ser `(soma dos pesos cobertos) ÷ (soma dos pesos pedidos)`. Com isso o mínimo mudou de
  unidade: `MIN_TECNOLOGIAS = 2` virou `MIN_PESO_PEDIDO = 4` (peso, não quantidade). Com o mínimo em 2 peso, uma vaga que pede só
  SQL (peso 2) cobria 100% (Equatorial foi a 88); com 4, Equatorial ficou em 53. Testado nas 23 vagas de `dados_serpapi/`.
  Com 3 só três vagas mudam, todas para pior (Equatorial 65, Suporte 47, Rosso 38). Fica 4 até o benchmark: o Heitor dá
  nota a 15-20 vagas e comparamos com a do agente para escolher `MIN_PESO_PEDIDO` e os `PESOS`.
- **Falta:** reiniciar o `adk web` e testar de novo com o código corrigido.

## Banco de dados (fase 3, 23/10/2026)

- **SQLite + SQLAlchemy** (`radar_estagio/banco.py`, arquivo `radar_estagio/radar_estagio.db`, ignorado pelo Git). MongoDB
  descartado: o briefing pede SQLAlchemy, o perfil já tem SQL/SQLAlchemy/PostgreSQL e o dado é uma tabela plana. Trocar
  para PostgreSQL depois só muda a string de conexão.
- **Tabela `vagas`, sem `id`:** a chave primária é a `chave` (título + empresa, sem acento e minúsculo), a mesma regra que o
  `buscar_vagas` usa para juntar duplicadas, porque o `job_id` da SerpApi muda de site para site. O banco recusa a
  segunda cópia. Custos aceitos: título editado vira vaga nova; vagas sem empresa e com o mesmo título colidem.
  Se entrar uma tabela de candidaturas, dá para voltar a `id` + `chave` única (o banco ainda é descartável).
- **A nota não é guardada:** é recalculada ao consultar. A conta é determinística (~1,5 ms por vaga), então não há risco
  de nota velha quando `PESOS`, perfil ou regras mudam. Se um dia precisar filtrar por nota no banco, adiciona a coluna.
- **Ligação com o agente:** o `buscar_vagas` chama `salvar_vagas` depois de dar a nota, e cada vaga volta com `nova`
  (True = entrou agora, False = já estava salva). A ordem continua pela nota. Se o banco falhar (`SQLAlchemyError`), a busca
  segue e as vagas voltam sem o campo `nova`; o agente só marca "Nova"/"Já vista" quando o campo existe. O import do
  banco fica dentro da função porque importar o `banco.py` cria o `.db`.
- **Sem coluna `status` por enquanto** (nova/vista/candidatei/descartei): uma coluna a mais, quando precisar.
- **Cuidado:** o `create_all` roda ao importar o `banco.py`, então importar o arquivo cria o `.db`.

## RAG no currículo (fase 4, 24/10/2026)

- **Para que serve:** a `analisar_vaga` mostra, ao lado da nota, os 3 trechos do currículo mais parecidos com a vaga
  ("onde você usou algo assim"). É **evidência, não decisão**: não muda a nota e o agente não escreve "você tem" a partir
  deles. As similaridades ficam espremidas (0,65 a 0,80), então não dá para usar um corte fixo; só serve para ordenar.
- **O que entra no índice:** o `perfil.json` (um só, o que também fecha a dúvida dos dois currículos), em 21 chunks:
  um por projeto, curso, grupo de habilidades, a pesquisa e a experiência. `objetivo`, `formacao`, `idiomas` e `fonte`
  ficam de fora: não são evidência de habilidade, e o `objetivo.areas` aparecia em quase toda busca.
- **Embeddings:** `gemini-embedding-001` (3072 números), com `task_type` `RETRIEVAL_DOCUMENT` nos chunks e
  `RETRIEVAL_QUERY` no pedido. O `task_type` melhorou a busca (o ruído saiu do topo e os projetos subiram).
- **ChromaDB** em `radar_estagio/chroma_db/` (fora do Git). O id do chunk é o hash SHA-1 do texto: texto igual não é
  gerado de novo, texto alterado vira chunk novo e o velho é apagado. A 2ª execução não chama o Gemini para os chunks.
  `dict.fromkeys` tira chunks repetidos antes, porque o Chroma recusa ids repetidos (já no `get`, não só no `add`).
- **Cuidado:** se mudar o modelo ou o `task_type` com o texto igual, o id não muda e os vetores velhos ficam: apagar a
  pasta `chroma_db/`.
- **A nota nunca depende do RAG:** se o Gemini ou o Chroma falharem (`APIError`, `ChromaError`, `ValueError` de falta de
  chave), a `analisar_vaga` devolve a nota sem o campo `evidencias`.
- **Bug que só o teste real achou:** `genai.Client().models.embed_content(...)` numa linha só fecha a conexão antes de a
  chamada sair (`Cannot send a request, as the client has been closed`). O cliente precisa ficar numa variável. O teste
  com embeddings falsos não pegava isso.
- **Dependências:** o `chromadb` subiu o `opentelemetry-*` para 1.45.1, mas o `google-adk 2.11.0` exige até 1.42.1. Voltei
  `api`, `sdk`, `semantic-conventions` e os exportadores `otlp` para 1.42.1 e tirei o `opentelemetry-exporter-otlp-common`
  (órfão). `pip check` limpo e `adk web` testado depois.
- **Como foi feito:** primeiro dois scripts de estudo (`experimento_embedding.py` e `experimento_rag.py`, só no disco, fora
  do Git), depois o módulo. A ordem ajudou: cada pedaço rodou e deu para ver o resultado antes do próximo.

## Servidor MCP (fase 7, 25-26/10/2026)

- **Papéis:** o **server** é o nosso `mcp_server.py` (oferece as 4 tools); o **host** é o agente rodando no ADK; o
  **client** é o `McpToolset` do ADK, o conector dentro do host. O agente só usa o servidor próprio, nada de terceiros.
- **As funções ficaram em `tools.py`:** o servidor as importa e registra com `add_tool`. O nome, a docstring e os tipos
  de cada função viram a descrição da tool, por isso as docstrings valem.
- **O servidor não tem memória:** a lista de tools é montada na memória a cada partida, pelo `add_tool` do código. A tool
  "sempre está lá" porque a linha está no arquivo, não porque algo foi guardado. O que persiste são arquivos (banco,
  índice do Chroma). No `stdio` quem conecta inicia o servidor como processo filho e o encerra no fim.
- **SDK `mcp` 2.3.0:** o `FastMCP` dos exemplos (`mcp.server.fastmcp`) não existe mais; a classe é `MCPServer`
  (`mcp.server.mcpserver`). Os campos do cliente são em `snake_case` (`input_schema`). Conferi no código instalado, não
  na documentação. O ADK 2.11 provavelmente foi feito pensando no SDK 1.x: funcionou, mas vale ficar de olho.
- **`stdio`: nada nas tools pode dar `print`** (a saída do processo é o protocolo). Logs saem pelo `stderr`.
- **Chaves:** o servidor é outro processo, então ele mesmo faz `load_dotenv` do `radar_estagio/.env` (Gemini e SerpApi).
- **O agente liga o servidor** com `StdioServerParameters` (o comando `python -m radar_estagio.mcp_server`, com
  `sys.executable` e `cwd` na raiz) dentro de `StdioConnectionParams` (timeout 30 s) dentro do `McpToolset`.
- **Quando o servidor nasce:** só na primeira mensagem, nunca ao subir o `adk web`, abrir a página, pedir o grafo ou criar
  a sessão (conferi olhando os processos). O `McpToolset(...)` do `agent.py` só guarda a receita; a cada mensagem o ADK
  monta o pedido ao Gemini com a lista de tools, e pedir a lista ao `McpToolset` (`get_tools`) conecta, o que executa o
  comando e cria o processo (`stdio_client`, no `mcp_session_manager.py` do ADK). Ao encerrar o `adk web`, o servidor
  encerra junto. Não achei a linha exata do ADK que dispara isso no começo da mensagem: o gatilho foi observado, não lido.
- **Testado:** cliente MCP de teste (lista as tools e chama `analisar_vaga` e `listar_vagas_salvas`) e `adk web` (o agente
  chamou `listar_vagas_salvas`, `analisar_vaga` e `buscar_vagas` pelo servidor). Nenhum processo do servidor sobrou depois.
- **`buscar_vagas` pelo agente (26/10/2026):** "tem estágio de backend?" chamou `buscar_vagas` com 3 termos e voltaram 4
  vagas (1 "Já vista", 3 "Nova"); o banco foi de 3 para 6. Gastou até 4 buscas da SerpApi.
- **Ganho de verdade:** para uso pessoal com um agente só, o MCP não muda a função (o agente já chamava as funções
  direto). O valor é outros hosts usarem o radar (ex.: Claude Desktop), vários agentes dividirem as tools (fase 9) e saber
  construir um servidor. Religar o agente foi escolha dele, para aprender o client do ADK.

## Vaga por print (fase 8, 27/10/2026)

- **Como funciona:** o Gemini lê a imagem sozinho (é multimodal), extrai o título e a descrição e o agente chama a
  `analisar_vaga` que já existia, pelo servidor MCP. Nenhuma tool nova e o modelo não mudou. A mudança foi só uma regra na
  `instruction` do `agent.py`: copiar o título e a descrição como estão no print, sem resumir nem reorganizar, e avisar
  **antes da nota** quando o print vem cortado ou ilegível.
- **Antes da regra:** o agente resumia e reorganizava o texto ("Responsabilidades" virou lista de posições, sumiram os
  emojis) e não avisou que o print cortava antes dos requisitos (culpou só o fato de ser um banco de talentos genérico).
- **Depois da regra, com o mesmo print:** texto copiado como está (com emojis e ordem) e aviso de print cortado antes da
  nota, que não mudou (36).
- **Testado com 3 prints, de 3 layouts:** banco de talentos da Invent (cortado nos requisitos), página da QCA (Recife,
  híbrido, Python e RPA; avisou que "Sobre a gente" estava cortado) e LinkedIn pequeno (Estágio IA em Aparecida de
  Goiânia; ignorou o ruído da tela e ficou com título, descrição, requisitos e benefícios). Cada um gastou 1 chamada do
  modelo e 1 de embedding.
- **Patch, token e chunk:** o modelo divide a imagem em *patches* por dentro (o par do token do texto). Chunk, no projeto,
  é o texto que se escolhe indexar e que tem um embedding associado.
- **O ponto fraco é a nota, não a leitura do print:** a `analisar_vaga` só recebe título e descrição, então não vê cidade
  nem modalidade (a QCA é em Recife, híbrida, e nada avisou), e o `nota.py` só enxerga as tecnologias de `TECNOLOGIAS`
  (Playwright, BeautifulSoup, Requests e RPA não contam, então "Lacunas: nenhuma" enganou; no LinkedIn, "modelos de
  linguagem" não virou LLMs e o inglês não entrou, e deu 100/100, provavelmente generoso).

## Refinos para o final

Coisas que ficam para uma passada de refino, depois das fases principais:

- [ ] **Busca por requisito (pedido pelo Heitor, 24/10/2026):** hoje a `analisar_vaga` pesquisa com o título + a descrição
  inteira, o que dilui o resultado. No teste, o ESL ("API de terceiros") nem apareceu e o projeto Radar entrou como 3º.
  Ideia: separar os requisitos da vaga e buscar por cada um; ou pesquisar só a parte de requisitos.
- [ ] **"Em estudo:" e "Lacunas:" vazios na resposta do agente:** a instrução manda mostrar "Em estudo" só se não estiver
  vazio, mas o modelo escreveu o rótulo sem nada. Reforçar a instrução ou montar o texto em código.
- [ ] **Chunks de uma palavra só** (`habilidades_parciais: Django`, `NLP`, `LLMs`): juntar em um chunk
  ("Habilidades em estudo: ...") se atrapalharem a busca.
- [ ] **Tirar um teste de verdade do `curriculo_rag`:** os testes foram rodados no terminal e nenhum ficou no repo.
- [ ] **A `analisar_vaga` ignora cidade e modalidade** (achado no print da QCA, em Recife, híbrida): avisar "presencial ou
  híbrida fora de Goiânia" como o filtro da busca faz, por exemplo com um `atencao` a mais ou lendo a cidade do texto.
- [ ] **A nota só vê as tecnologias da lista `TECNOLOGIAS`:** acrescentar as que apareceram nas vagas de teste (Playwright,
  BeautifulSoup, Requests, RPA) e tratar "modelos de linguagem" como LLMs e "inglês para leitura" como requisito.
- [ ] **Demonstração do servidor MCP com o Claude Desktop como host** (opcional).
- [ ] **Benchmark (fase 10):** dar nota a 15-20 vagas e comparar com a do agente.

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

| Fase | O que é | Estado |
|---|---|---|
| 1 | `buscar_vagas` com dados falsos | feita |
| 2 | API real (SerpApi) e filtro | feita |
| 3 | Banco de dados (SQLAlchemy) | feita |
| 4 | Currículo em chunks e embeddings (RAG) | feita (24/10/2026): `curriculo_rag.py`, ligada à `analisar_vaga`; o refino da busca fica para o final |
| 5 | Nota de compatibilidade e lacunas | feita: nota em código e a tool `analisar_vaga` (com as evidências da fase 4) |
| 6 | API FastAPI | **adiada** (25/10/2026): só se houver deploy ou interface própria. O uso é pessoal, pelo `adk web`, e o FastAPI já está em 2 projetos dele |
| 7 | Servidor MCP | feita (25-26/10/2026): `mcp_server.py` e o agente ligado a ele; falta só a demonstração com o Claude Desktop (opcional) |
| 8 | Vaga por print (multimodal) | feita (27/10/2026): sem tool nova, só a `instruction` do agente; limitações da nota anotadas nos refinos |
| 9 | Multiagente | não começou |
| 10 | Benchmark, README final, demo e deploy | README parte 1 feita; benchmark e o resto ficam para o fim |

Detalhes de cada fase, em ordem:

- **Fase 1: concluída e publicada.** `buscar_vagas` com 18 vagas falsas, ligada ao agente e testada no `adk web`.
  `.env` fora do Git. Repo no GitHub ligado (`origin/main`). Commits da fase:
  `e890987` (estrutura), `5bf2c6c` (`buscar_vagas`), `0262341` (agente + testes no `adk web`).
- **Fase 2: concluída e publicada (16/10/2026).** Começou com o Adzuna (`b8e3d02..de4f726`), mas a fonte final é o
  **Google Jobs via SerpApi** (ver a seção no topo). `buscar_vagas` busca, converte, filtra (TI, estágio, cidade, área,
  linguagem) e foi testada no `adk web`. Está na `main` do GitHub (`cd4459e`). Commits da troca: `63b17de` (SerpApi),
  `4bd18ab` (`.gitignore`), `cd4459e` (remove o Adzuna, atualiza as notas). O código do Adzuna está em `211a37e`.
- **Fase 3: concluída e publicada (23/10/2026).** Banco SQLite com SQLAlchemy (`banco.py`): `salvar_vagas`,
  `consultar_vagas`, `buscar_vagas` marcando `nova`, e a tool `listar_vagas_salvas` (`1bff847`, `6b61d99`, `1dd3db6`,
  `7655d99`). Testado no `adk web`: 1ª busca "Nova", 2ª "Já vista", e "o que eu já vi de backend?" lê o banco sem gastar
  SerpApi. Decisões na seção "Banco de dados (fase 3)".
- **Nota (22/10/2026):** tecnologias com peso, `redes` sem penalidade (`02dbdf2`, `43f9c99`). `PESOS` e `MIN_PESO_PEDIDO`
  são palpites até o benchmark (vaga Java/JavaScript "Web Scraping" com nota 90 é um caso para ele).
- **Fase 5: feita sem o RAG.** Feito (a análise de compatibilidade da fase 5): `perfil.json`, `carregar_perfil` e a análise de compatibilidade na instruction
  (nota, "Você já tem", lacunas), mesclados na `main` pelo PR #1 (`ac761a7`). Nota calculada em código por palavras-chave (20/10/2026), testada no `adk web` com 19 vagas.
- **`analisar_vaga` (fase 5, 23/10/2026):** tool que recebe `titulo` e `descricao` de uma vaga colada na conversa, monta o
  dicionário com `_detectar_area` e `_detectar_linguagens`, e chama o `calcular_nota` com o perfil. Título obrigatório: sem
  ele o agente pergunta (decisão por simplicidade). Não busca nem salva. Testada no `adk web`: vaga com título (nota 91,
  lacuna Kubernetes) e vaga sem título (o agente pediu o título).
- **Fase 10, parte 1: feita (19/10/2026).** README publicado (`72651f4`) com banner (`docs/banner.svg`), badges,
  diagramas Mermaid e `.env.example`; aviso de "em desenvolvimento" no topo.
- **Fase 10, parte 2: no fim do projeto.** Atualizar o README com o estado final (tirar o aviso de desenvolvimento,
  roadmap, exemplo real de resposta no lugar do ilustrativo, seção de decisões a partir deste `NOTAS.md`).
- **Fase 4: feita (24/10/2026).** RAG no currículo: `curriculo_rag.py` (`1d44dcd` dependências, `5dd57d3` módulo,
  `f149b40` ligado à `analisar_vaga`). Decisões e aprendizados na seção "RAG no currículo (fase 4)".
- **Fase 6 adiada (25/10/2026):** o plano de 10 fases foi um ponto de partida, não uma exigência. Uma API HTTP só serve
  se algo fora do `adk web` precisar chamar o radar (tela própria, outro programa, deploy), e hoje nada disso existe.
  Se um dia houver deploy, entra uma versão fina (2 ou 3 endpoints) em cima do que já existe.
- **Fase 7: feita (25-26/10/2026).** Servidor MCP em `mcp_server.py` (`26c729e` dependência, `65a05ae` e `b7b3e8b` o
  servidor, `9d09d99` o agente ligado a ele). Decisões na seção "Servidor MCP (fase 7)".
- **Fase 8: feita (27/10/2026).** Vaga por print: o `gemini-3.5-flash` já aceita imagem, então não precisou de tool nem de
  trocar o modelo (`5f98e48`). Decisões e testes na seção "Vaga por print (fase 8)".
- **Próximo:** fase 9 (multiagente) a decidir: ele já tem um projeto multiagente do bootcamp, então pode ficar de fora. O
  benchmark (fase 10) e os refinos da seção "Refinos para o final" ficam para o fim do projeto. A fase 9 ainda não está
  descrita aqui. Cidade "Não informada" em vagas remotas vem da SerpApi.

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
- **Resultado nas respostas reais salvas:** Goiânia 9 de 20 passam; nacional 3 de 20 (as de cidade desconhecida ou remoto).
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
- **Import relativo:** `tools.py` agora usa import relativo, então rodar `python radar_estagio/tools.py` direto não funciona mais;
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
  O import de `dados_falsos` saiu do `tools.py`.
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
- [x] Fase 4: decidir como usar os dois currículos (IA e dev): comparar com os dois ou unificar. Resolvido: o RAG usa só o
  `perfil.json`.
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
