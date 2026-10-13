# Notas de aprendizado e decisões

Rascunho para virar a seção de decisões do README (fase 10).

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
- **Fase 2: em andamento.** Começou o filtro em `radar_estagio/filtro.py` (ainda não commitado, ainda não ligado à
  `buscar_vagas`). Falta: validar o filtro contra os comentários `# filtro:` dos dados falsos, ligá-lo dentro da
  `buscar_vagas` e trocar os dados falsos por uma API real.

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
- [ ] Commitar `radar_estagio/filtro.py` e a alteração pendente em `agent.py` quando o filtro estiver validado.
- [ ] Conferir se, na pergunta "vaga de astronauta", o agente fez a segunda busca que a `instruction` pede.
- [ ] Opcional: trocar o exemplo da docstring de `buscar_vagas` por um tema menos "copiável".
- [ ] Fase 2: ler a documentação das APIs de vagas (Adzuna, Remotive) e confirmar se cobrem estágio no Brasil.
- [ ] Fase 2: validar o filtro (`filtro.py`) contra os comentários `# filtro:` dos dados falsos e ligá-lo dentro de
  `buscar_vagas` (ele roda por dentro, não é uma tool). Áreas "dev" definidas no código: backend, fullstack,
  embarcados, ia. Teste rodado contra os dados falsos: 16 de 18 batem. As vagas 11 (mobile, Dart) e 18 (frontend,
  JavaScript) passam no filtro atual, mas **foi decisão minha deixar mobile e frontend de fora** (não são meu interesse).
  Quando voltar ao filtro: o jeito honesto de barrá-las é pôr `mobile` e `frontend` em `AREAS_EXCLUIDAS`
  (não é "dev sem linguagem aceita", é "área que não quero"); aí o gabarito `# filtro:` continua barrando as duas.
  Filtro pausado por enquanto.
- [ ] Fase 2: restringir o `try/except` só à chamada externa e capturar exceções específicas.
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
