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

## Pendências

- [ ] Assinatura: conferir `list[str] | None = None` (a docstring diz "Se omitido, devolve todas").
- [ ] Tirar (ou proteger com `if __name__ == "__main__":`) o código solto no fim do `tools.py`. (Já protegido com `__main__`; conferir.)
- [ ] Escrever o `agent.py` (nome, modelo, description, instruction, `tools=[buscar_vagas]`) e testar no `adk web`.
- [ ] Ideia para o `agent.py`: interesses gerais (backend, IA, dados) na `instruction`, para quando o usuário não disser o tema.
- [ ] Criar o repositório no GitHub e conectar o repo local (`git remote add` + `git push`).
- [ ] Fase 2: escrever o filtro como função separada, testada contra os comentários `# filtro:` dos dados falsos.
- [ ] Fase 4: decidir como usar os dois currículos (IA e dev): comparar com os dois ou unificar.
- [ ] Ideia: `require_confirmation` do ADK (experimental) se algum dia houver uma tool que aja no mundo.
