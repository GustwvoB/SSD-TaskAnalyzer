# CONTEXT_RULES — Regras para agentes de IA

Estas regras valem para qualquer assistente de IA (ChatGPT, Gemini, Copilot, Claude...) que gerar ou alterar código neste repositório. Elas precisam ser enviadas junto com a especificação (`specs/task_analyzer_spec.md`) antes de qualquer pedido de código.

## 1. Contrato fixo

- Arquivo de implementação: `src/task_analyzer.py`
- Função pública: `analyze_tasks`
- Exceção customizada: `TaskValidationError`
- O comportamento esperado está em `specs/task_analyzer_spec.md`, que é a fonte da verdade.

## 2. Diretrizes arquiteturais (obrigatórias)

- Python 3.11 ou superior.
- Type hints em 100% das funções, métodos e parâmetros.
- Princípio de responsabilidade única (SRP) e código limpo (PEP 8).
- Docstrings no padrão Google style para módulos, classes e funções.
- Funções pequenas, coesas e com um único propósito; evitar scripts monolíticos.
- Tratamento de exceções específico e com mensagens claras (nunca usar `except` genérico sem tratamento adequado).
- Prevenir divisão por zero, conforme a especificação.
- Logs com o módulo padrão `logging` (nunca `print()`).
- Nomes de variáveis e funções descritivos; código legível e fácil de manter.
- Comentários e docstrings em português.

## 3. Proibições explícitas

- Não usar bibliotecas externas não autorizadas (apenas a biblioteca padrão do Python e o `pytest` nos testes, salvo autorização explícita).
- Não alterar, remover ou adaptar os testes de `tests/test_harness.py` nem os cenários da especificação.
- Não modificar a estrutura de pastas do repositório.
- Não persistir dados em arquivos ou bancos de dados (o módulo é stateless).
- Não alterar o nome nem os parâmetros das funções públicas sem autorização.
- Não gerar código sem testes correspondentes para novas funcionalidades.
- Não inserir código duplicado ou desnecessário.
- Não assumir comportamentos que não estejam no contrato. Em caso de dúvida, o agente deve sinalizar a ambiguidade em vez de "inventar" um comportamento.

## 4. Regras de interação com a IA

- Fornecer sempre o contexto completo antes de pedir código (este arquivo e a especificação).
- Validar se a IA entendeu o contrato antes de aceitar o código gerado.
- Pedir explicações quando houver dúvida sobre a solução proposta.
- Revisar criticamente todo código gerado; nada é aceito automaticamente.
- Rejeitar respostas que violem as proibições acima ou que fujam do contrato.
- Se a IA sugerir mudar um teste para o código passar, a resposta deve ser rejeitada: o que se corrige é o código.
