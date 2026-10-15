"""Test Harness do TaskAnalyzer.

Traduz os cenarios de aceite da especificacao SDD em testes automatizados.
"""

from datetime import datetime, timezone

import pytest

from src.task_analyzer import TaskValidationError, analyze_tasks


def utc(dia: int, hora: int) -> datetime:
    """Cria um datetime em UTC no mes de setembro de 2026.

    Args:
        dia: Dia do mes.
        hora: Hora do dia (0 a 23).

    Returns:
        Datetime com fuso UTC.
    """
    return datetime(2026, 9, dia, hora, 0, tzinfo=timezone.utc)


def criar_tarefa(
    id_tarefa: int,
    prioridade: str,
    status: str,
    data_criacao: datetime,
    prazo: datetime,
    data_conclusao: datetime | None = None,
) -> dict:
    """Monta uma tarefa no formato definido pelo contrato.

    Args:
        id_tarefa: Identificador da tarefa.
        prioridade: "baixa", "media" ou "alta".
        status: "concluida", "pendente" ou "cancelada".
        data_criacao: Data de criacao da tarefa.
        prazo: Data limite de conclusao.
        data_conclusao: Data de conclusao (apenas para tarefas concluidas).

    Returns:
        Dicionario representando a tarefa.
    """
    return {
        "id_tarefa": id_tarefa,
        "titulo": f"Tarefa {id_tarefa}",
        "prioridade": prioridade,
        "status": status,
        "data_criacao": data_criacao,
        "data_inicio": None,
        "data_conclusao": data_conclusao,
        "prazo": prazo,
    }


def test_cenario_1_sucesso() -> None:
    """Cenario 1: tarefas validas devem gerar as metricas corretas."""
    tarefas = [
        # 2h de duracao, concluida dentro do prazo
        criar_tarefa(1, "alta", "concluida", utc(1, 8), utc(1, 12), utc(1, 10)),
        # 5h de duracao, concluida 1h depois do prazo (atrasada)
        criar_tarefa(2, "media", "concluida", utc(1, 8), utc(1, 12), utc(1, 13)),
        # pendente, nao entra nas medias
        criar_tarefa(3, "baixa", "pendente", utc(1, 8), utc(1, 18)),
        # 4h de duracao, concluida exatamente no prazo (nao e atraso)
        criar_tarefa(4, "alta", "concluida", utc(1, 8), utc(1, 12), utc(1, 12)),
    ]

    resultado = analyze_tasks(tarefas)

    assert resultado["total_tarefas"] == 4
    assert resultado["total_concluidas"] == 3
    assert resultado["total_pendentes"] == 1
    assert resultado["tempo_medio_conclusao_horas"] == pytest.approx(3.67)

    por_prioridade = resultado["tempo_medio_conclusao_por_prioridade_horas"]
    assert por_prioridade["alta"] == pytest.approx(3.0)
    assert por_prioridade["media"] == pytest.approx(5.0)
    assert por_prioridade["baixa"] == 0.0

    assert resultado["taxa_atraso_percentual"] == pytest.approx(33.33)


def test_cenario_2_data_conclusao_anterior_a_criacao() -> None:
    """Cenario 2: data_conclusao menor que data_criacao deve dar erro."""
    tarefas = [
        criar_tarefa(1, "alta", "concluida", utc(1, 10), utc(1, 12), utc(1, 8)),
    ]

    with pytest.raises(TaskValidationError):
        analyze_tasks(tarefas)