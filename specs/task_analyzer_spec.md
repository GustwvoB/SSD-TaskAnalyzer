# Especificação SDD — TaskAnalyzer

**Versão:** 1.1
**Autor:** Gustavo Barbosa Oliveira
**Disciplina:** Bootcamp III — Análise e Desenvolvimento de Sistemas (UniCEUB)

## 1. Visão geral

O TaskAnalyzer é um módulo Python que recebe uma lista de tarefas e devolve métricas de produtividade: quantidade de tarefas por situação, tempo médio de conclusão (geral e por prioridade) e taxa de atraso.

Este documento é o contrato que o código gerado por IA precisa seguir. Se alguma coisa não estiver escrita aqui, a IA não deve inventar: deve sinalizar a dúvida (regra definida no `CONTEXT_RULES.md`).

O módulo é *stateless*: não lê nem grava arquivos e não usa banco de dados.

## 2. O que mudou em relação à Fase 1 (v1.0 para v1.1)

Ao montar o Test Harness, o contrato foi refinado. Os pontos que mudaram:

| Item | v1.0 (Fase 1) | v1.1 (esta versão) |
|---|---|---|
| Unidade do tempo médio | minutos (`tempo_medio_conclusao_min`) | horas (`tempo_medio_conclusao_horas`) |
| Contagens | `quantidade_tarefas` | `total_tarefas`, `total_concluidas` e `total_pendentes` |
| Divisão por zero | disparava exceção | retorna `0.0`, sem exceção |
| Exceção | "exceção específica", sem nome | `TaskValidationError` |
| Pendente com prazo vencido | contava como atraso | não conta; a taxa de atraso olha só tarefas concluídas |
| Função pública | sem nome definido | `analyze_tasks` |
| Indicadores por prioridade | descrição genérica | tempo médio por prioridade, em dicionário com chaves fixas |

O motivo da mudança do atraso: se a taxa dependesse da data de hoje, a mesma entrada daria resultados diferentes em dias diferentes. Assim, o resultado depende só dos dados recebidos.

## 3. Contrato da interface

### 3.1 Função pública

`analyze_tasks(tarefas: list[dict]) -> dict`

### 3.2 Entrada

Cada tarefa é um dicionário com os campos abaixo. Os valores de texto são escritos sem acento (`media`, `concluida`) para evitar problemas de digitação.

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `id_tarefa` | int | Sim | Inteiro positivo |
| `titulo` | str | Sim | Não pode ser vazio |
| `prioridade` | str | Sim | `baixa`, `media` ou `alta` |
| `status` | str | Sim | `concluida`, `pendente` ou `cancelada` |
| `data_criacao` | datetime | Sim | Com fuso UTC |
| `data_inicio` | datetime ou None | Não | Só informativo, não entra nos cálculos |
| `data_conclusao` | datetime ou None | Condicional | Obrigatória quando o status é `concluida` |
| `prazo` | datetime | Sim | Data limite para conclusão, com fuso UTC |

### 3.3 Saída

A função devolve um dicionário com estas chaves:

| Chave | Tipo | Descrição |
|---|---|---|
| `total_tarefas` | int | Todas as tarefas recebidas, incluindo as canceladas |
| `total_concluidas` | int | Tarefas com status `concluida` |
| `total_pendentes` | int | Tarefas com status `pendente` |
| `tempo_medio_conclusao_horas` | float | Média geral de tempo das tarefas concluídas |
| `tempo_medio_conclusao_por_prioridade_horas` | dict | Média por prioridade; sempre tem as chaves `baixa`, `media` e `alta` |
| `taxa_atraso_percentual` | float | Percentual (0 a 100) de tarefas concluídas com atraso |

### 3.4 Regras de negócio

1. O tempo de conclusão de uma tarefa é `data_conclusao` menos `data_criacao`, convertido para horas.
2. Só tarefas `concluida` entram nas médias e na taxa de atraso.
3. Uma tarefa concluída está atrasada quando `data_conclusao` é **maior** que o `prazo`. Concluir exatamente no prazo não é atraso.
4. Taxa de atraso = tarefas concluídas com atraso ÷ `total_concluidas` × 100.
5. Tarefas `cancelada` contam apenas em `total_tarefas`. Não entram em concluídas, pendentes, médias nem na taxa.
6. Se não houver tarefas concluídas (lista vazia, só pendentes ou só canceladas), as médias e a taxa valem `0.0`, sem lançar exceção. O mesmo vale para uma prioridade que não tenha nenhuma tarefa concluída.
7. Lista vazia é uma entrada válida e retorna todos os valores zerados.
8. Os resultados `float` são arredondados para 2 casas decimais apenas no final (sem arredondar nos cálculos intermediários).

### 3.5 Validação e erro

A função lança `TaskValidationError` (exceção customizada que herda de `Exception`) quando:

- a entrada não é uma lista, ou uma tarefa não é um dicionário ou está sem algum campo obrigatório;
- `id_tarefa` não é um inteiro positivo ou `titulo` está vazio;
- `prioridade` ou `status` têm valores fora dos aceitos;
- `data_criacao` ou `prazo` não são `datetime`;
- o status é `concluida` e não há `data_conclusao`;
- existe `data_conclusao` anterior à `data_criacao`.

A mensagem do erro deve informar o `id_tarefa` e qual foi o problema encontrado.

## 4. Cenários de aceite

### Cenário 1 — Sucesso

**Dado** o conjunto de tarefas abaixo (todas criadas em 01/09/2026, horários em UTC):

| id | Prioridade | Status | Criada | Prazo | Concluída | Tempo | Situação |
|---|---|---|---|---|---|---|---|
| 1 | alta | concluida | 08h | 12h | 10h | 2 h | no prazo |
| 2 | media | concluida | 08h | 12h | 13h | 5 h | atrasada |
| 3 | baixa | pendente | 08h | 18h | — | — | — |
| 4 | alta | concluida | 08h | 12h | 12h | 4 h | no prazo (exatamente) |

**Quando** `analyze_tasks` é executada com essa lista,

**Então** o resultado deve ser:

- `total_tarefas` = 4, `total_concluidas` = 3, `total_pendentes` = 1
- `tempo_medio_conclusao_horas` = 3.67
- tempo médio por prioridade: `alta` = 3.0, `media` = 5.0, `baixa` = 0.0
- `taxa_atraso_percentual` = 33.33

### Cenário 2 — Exceção/Erro

**Dado** uma tarefa concluída cuja `data_conclusao` é anterior à `data_criacao`,

**Quando** `analyze_tasks` é executada,

**Então** deve ser lançada `TaskValidationError`.

### Cenário 3 — Casos de borda

**Dado** uma lista vazia, ou uma lista com apenas tarefas pendentes,

**Quando** `analyze_tasks` é executada,

**Então** as médias e a taxa de atraso valem `0.0` e nenhuma exceção é lançada.

## 5. Test Harness

Os testes ficam em `tests/test_harness.py` e traduzem os cenários acima:

| Teste | Cenário |
|---|---|
| `test_cenario_1_sucesso` | Cenário 1 |
| `test_cenario_2_data_conclusao_anterior_a_criacao` | Cenário 2 |
| `test_borda_lista_vazia` | Cenário 3 |
| `test_borda_apenas_pendentes` | Cenário 3 |

Para executar: `python -m pytest -v`

Regra importante: a IA não pode alterar os testes. Se um teste falhar, o que se corrige é o código.

## 6. Referências

- Regras de governança para a IA: `CONTEXT_RULES.md`
- Código-fonte (gerado via IA e homologado por humano): `src/task_analyzer.py`
