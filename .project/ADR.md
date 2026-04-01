# Architecture Decision Records

Global technical decisions for this project.
Decisions scoped to one PRD belong in `.project/{prd}/architecture.md`.
Decisions scoped to one spec belong in `.project/{prd}/.specs/{spec}/design.md`.

For the entry template, see `.claude/skills/adr/templates/adr-entry.md`.

---

<!-- Add new ADRs below, newest first -->

## ADR-007: pytest as the sole test framework
**Status:** Accepted
**Date:** 2026-03-30
**Context:** pytest offers fixtures, parametrize, and a rich plugin ecosystem that suits both unit and integration tests.
**Decision:** Use pytest exclusively. No unittest subclassing.
**Consequences:** Test files follow `test_*.py` naming. Fixtures are defined in `conftest.py`.

---

## ADR-006: Google-style docstrings e type hints obrigatórios
**Status:** Accepted
**Date:** 2026-03-30
**Context:** Consistência de documentação e tipagem melhora suporte a IDE, geração de docs e onboarding.
**Decision:** Todas as funções, métodos e classes públicas devem ter docstrings no estilo Google (descrição, Args, Returns, Raises) e type hints completos. Aplicado via linting no CI.
**Consequences:** Código levemente mais verboso, mas com muito melhor descoberta e manutenibilidade.

---

## ADR-005: Rastreamento de custo de tokens em todo Run
**Status:** Accepted
**Date:** 2026-03-30
**Context:** Decisões de seleção de modelo exigem comparar uso e custo de tokens entre experimentos, não apenas métricas de qualidade.
**Decision:** Todo resultado de `Run` captura `input_tokens`, `output_tokens` e opcionalmente `cost_usd` se uma tabela de preços for fornecida. Esses dados são enviados ao LangSmith junto com as pontuações de avaliação.
**Consequences:** O Runner deve aceitar uma config de preços opcional. Os dados de token são observacionais — o Assayer não cobra usuários.

---

## ADR-004: Metric como abstração separada de Evaluator
**Status:** Accepted
**Date:** 2026-03-30
**Context:** Evaluators pontuam previsões individuais; métricas agregam pontuações em todo o dataset. Misturar os dois violaria o Single Responsibility Principle.
**Decision:** Separar `Evaluator` (pontuação por exemplo) de `Metric` (agregação em nível de dataset). Ambos são independentemente extensíveis.
**Consequences:** Usuários compõem pipelines selecionando evaluators e métricas de forma independente.

---

## ADR-003: Evaluator como ponto de extensão principal (Open/Closed Principle)
**Status:** Accepted
**Date:** 2026-03-30
**Context:** O framework deve suportar tipos de evaluator customizados sem modificar arquivos core da biblioteca.
**Decision:** Definir uma classe base abstrata `Evaluator`. Todos os evaluators built-in e definidos pelo usuário devem subclassificá-la. Um registro permite que evaluators sejam buscados por nome em tempo de execução.
**Consequences:** Adicionar um novo tipo de evaluator requer apenas subclassificar e registrar — sem alterações no Runner ou pipeline core.

---

## ADR-002: LangSmith como único backend de observabilidade
**Status:** Accepted
**Date:** 2026-03-30
**Context:** Precisamos de rastreamento de experimentos, gerenciamento de datasets e visualização de resultados sem construir uma UI customizada.
**Decision:** Usar LangSmith exclusivamente como backend para armazenar runs, experimentos e datasets.
**Consequences:** Usuários precisam de conta e API key do LangSmith. Troca de backend é preocupação futura e está fora do escopo.

---

## ADR-001: Python 3.11.13 como runtime mínimo
**Status:** Accepted
**Date:** 2026-03-30
**Context:** O projeto usa recursos modernos do Python (match statements, tipo `Self`, `tomllib`, mensagens de erro melhoradas).
**Decision:** Exigir Python 3.11.13 como versão mínima.
**Consequences:** Usuários em versões mais antigas do Python não são suportados. CI deve fixar na 3.11.13.
