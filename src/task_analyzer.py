"""Módulo para análise de tarefas e métricas de produtividade.

Este módulo implementa a lógica stateless para processar uma lista de dicionários
de tarefas, validá-los conforme regras estritas e retornar indicadores consolidados
de produtividade, como tempos médios de conclusão e taxa de atraso.
"""

from datetime import datetime
import logging
from typing import Any

# Configuração do logger conforme as diretrizes (proibido o uso de print())
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constantes de módulo para valores fixos como tuplas (garantindo ordem determinística)
PRIORIDADES_VALIDAS: tuple[str, ...] = ("baixa", "media", "alta")
STATUS_VALIDOS: tuple[str, ...] = ("concluida", "pendente", "cancelada")


class TaskValidationError(Exception):
    """Exceção customizada disparada quando há falha de validação nos dados das tarefas."""

    pass


def _validar_tipo_dicionario(tarefa: Any) -> int:
    """Valida se a tarefa é um dicionário e extrai o id_tarefa.

    Args:
        tarefa (Any): Objeto a ser validado.

    Returns:
        int: O identificador da tarefa.

    Raises:
        TaskValidationError: Se não for dicionário, se o id estiver ausente
            ou se não for um inteiro positivo.
    """
    if not isinstance(tarefa, dict):
        raise TaskValidationError(
            f"Tarefa inválida: esperado dicionário, obtido {type(tarefa).__name__}"
        )
    id_tarefa = tarefa.get("id_tarefa")
    if id_tarefa is None:
        raise TaskValidationError(
            "Tarefa inválida: campo obrigatório ausente: id_tarefa"
        )
    if not isinstance(id_tarefa, int) or id_tarefa <= 0:
        raise TaskValidationError(
            f"Tarefa ID {id_tarefa}: id_tarefa deve ser um inteiro positivo"
        )
    return id_tarefa


def _validar_campos_obrigatorios(tarefa: dict, id_tarefa: int) -> None:
    """Valida a presença e os tipos dos campos obrigatórios básicos da tarefa.

    Args:
        tarefa (dict): Dicionário com os dados da tarefa.
        id_tarefa (int): Identificador da tarefa para mensagens de erro.

    Raises:
        TaskValidationError: Se faltar algum campo ou o tipo estiver incorreto.
    """
    campos_obrigatorios = {
        "titulo": str,
        "prioridade": str,
        "status": str,
        "data_criacao": datetime,
        "prazo": datetime,
    }
    for campo, tipo in campos_obrigatorios.items():
        if campo not in tarefa:
            raise TaskValidationError(
                f"Tarefa ID {id_tarefa}: campo obrigatório ausente: {campo}"
            )
        if not isinstance(tarefa[campo], tipo):
            raise TaskValidationError(
                f"Tarefa ID {id_tarefa}: campo '{campo}' deve ser do tipo {tipo.__name__}"
            )


def _validar_valores_dominio(tarefa: dict, id_tarefa: int) -> None:
    """Valida o conteúdo de domínio para título, prioridade e status.

    Args:
        tarefa (dict): Dicionário com os dados da tarefa.
        id_tarefa (int): Identificador da tarefa para mensagens de erro.

    Raises:
        TaskValidationError: Se o título estiver vazio ou se prioridade/status forem inválidos.
    """
    if not tarefa["titulo"].strip():
        raise TaskValidationError(
            f"Tarefa ID {id_tarefa}: título não pode estar vazio"
        )
    if tarefa["prioridade"] not in PRIORIDADES_VALIDAS:
        raise TaskValidationError(
            f"Tarefa ID {id_tarefa}: prioridade inválida '{tarefa['prioridade']}'. "
            f"Valores aceitos: {PRIORIDADES_VALIDAS}"
        )
    if tarefa["status"] not in STATUS_VALIDOS:
        raise TaskValidationError(
            f"Tarefa ID {id_tarefa}: status inválido '{tarefa['status']}'. "
            f"Valores aceitos: {STATUS_VALIDOS}"
        )


def _validar_datas_e_consistencia(tarefa: dict, id_tarefa: int) -> None:
    """Valida regras de preenchimento e consistência temporal de datas.

    Args:
        tarefa (dict): Dicionário com os dados da tarefa.
        id_tarefa (int): Identificador da tarefa para mensagens de erro.

    Raises:
        TaskValidationError: Se data_conclusao estiver ausente ou None quando concluída,
            se o tipo for inválido, ou se data_conclusao for anterior à data_criacao
            independentemente do status.
    """
    status = tarefa["status"]
    data_criacao = tarefa["data_criacao"]

    if status == "concluida":
        if "data_conclusao" not in tarefa or tarefa["data_conclusao"] is None:
            raise TaskValidationError(
                f"Tarefa ID {id_tarefa}: data_conclusao é obrigatória para tarefas concluídas"
            )

    if "data_conclusao" in tarefa and tarefa["data_conclusao"] is not None:
        data_conclusao = tarefa["data_conclusao"]
        if not isinstance(data_conclusao, datetime):
            raise TaskValidationError(
                f"Tarefa ID {id_tarefa}: data_conclusao deve ser do tipo datetime"
            )
        if data_conclusao < data_criacao:
            raise TaskValidationError(
                f"Tarefa ID {id_tarefa}: data_conclusao anterior à data_criacao"
            )


def _validar_tarefa(tarefa: dict) -> None:
    """Valida individualmente os campos, tipos e regras de uma tarefa.

    Args:
        tarefa (dict): Dicionário contendo os dados da tarefa.

    Raises:
        TaskValidationError: Se houver qualquer violação de regra ou tipo.
    """
    id_tarefa = _validar_tipo_dicionario(tarefa)
    _validar_campos_obrigatorios(tarefa, id_tarefa)
    _validar_valores_dominio(tarefa, id_tarefa)
    _validar_datas_e_consistencia(tarefa, id_tarefa)


def _calcular_tempo_horas(data_criacao: datetime, data_conclusao: datetime) -> float:
    """Calcula o tempo decorrido entre a criação e a conclusão em horas.

    Args:
        data_criacao (datetime): Data e hora de criação.
        data_conclusao (datetime): Data e hora de conclusão.

    Returns:
        float: Tempo decorrido em horas.
    """
    delta = data_conclusao - data_criacao
    return delta.total_seconds() / 3600.0


def _calcular_media_segura(soma: float, quantidade: int) -> float:
    """Calcula a média com prevenção de divisão por zero.

    Args:
        soma (float): Soma total dos valores.
        quantidade (int): Quantidade de elementos.

    Returns:
        float: Média arredondada para 2 casas decimais ou 0.0 se quantidade for zero.
    """
    if quantidade == 0:
        return 0.0
    return round(soma / quantidade, 2)


def _calcular_taxa_segura(atrasos: int, total_concluidas: int) -> float:
    """Calcula a taxa percentual de atraso com prevenção de divisão por zero.

    Args:
        atrasos (int): Número de tarefas concluídas com atraso.
        total_concluidas (int): Total de tarefas concluídas.

    Returns:
        float: Percentual de atraso arredondado para 2 casas decimais ou 0.0 se zero.
    """
    if total_concluidas == 0:
        return 0.0
    return round((atrasos / total_concluidas) * 100.0, 2)


def _processar_tarefa_concluida(
    tarefa: dict, acumulador_prioridade: dict[str, dict[str, Any]]
) -> tuple[float, int]:
    """Processa métricas de tempo e atraso para uma tarefa concluída.

    Args:
        tarefa (dict): Dicionário da tarefa concluída.
        acumulador_prioridade (dict): Dicionário com somas e quantidades por prioridade.

    Returns:
        tuple[float, int]: Tupla contendo o tempo em horas e indicador de atraso (0 ou 1).
    """
    data_criacao = tarefa["data_criacao"]
    data_conclusao = tarefa["data_conclusao"]
    prazo = tarefa["prazo"]
    prioridade = tarefa["prioridade"]

    tempo_horas = _calcular_tempo_horas(data_criacao, data_conclusao)
    acumulador_prioridade[prioridade]["soma_tempo"] += tempo_horas
    acumulador_prioridade[prioridade]["quantidade"] += 1

    atrasada = 1 if data_conclusao > prazo else 0
    return tempo_horas, atrasada


def analyze_tasks(tarefas: list[dict]) -> dict:
    """Analisa uma lista de tarefas e retorna métricas de produtividade consolidadas.

    Args:
        tarefas (list[dict]): Lista contendo os dicionários de tarefas.

    Returns:
        dict: Dicionário contendo as métricas calculadas:
            - total_tarefas (int)
            - total_concluidas (int)
            - total_pendentes (int)
            - tempo_medio_conclusao_horas (float)
            - tempo_medio_conclusao_por_prioridade_horas (dict)
            - taxa_atraso_percentual (float)

    Raises:
        TaskValidationError: Se a entrada não for uma lista ou se qualquer tarefa
            violar as regras de validação.
    """
    if not isinstance(tarefas, list):
        raise TaskValidationError(
            f"Entrada inválida: esperado list, obtido {type(tarefas).__name__}"
        )

    logger.info("Iniciando análise de %d tarefa(s).", len(tarefas))

    for tarefa in tarefas:
        _validar_tarefa(tarefa)

    total_tarefas = len(tarefas)
    total_concluidas = 0
    total_pendentes = 0
    soma_tempo_geral = 0.0
    atrasos_count = 0

    acumulador_prioridade = {
        prio: {"soma_tempo": 0.0, "quantidade": 0} for prio in PRIORIDADES_VALIDAS
    }

    for tarefa in tarefas:
        status = tarefa["status"]
        if status == "concluida":
            total_concluidas += 1
            tempo_h, atrasada = _processar_tarefa_concluida(
                tarefa, acumulador_prioridade
            )
            soma_tempo_geral += tempo_h
            atrasos_count += atrasada
        elif status == "pendente":
            total_pendentes += 1

    tempo_medio_conclusao_geral = _calcular_media_segura(
        soma_tempo_geral, total_concluidas
    )
    taxa_atraso = _calcular_taxa_segura(atrasos_count, total_concluidas)

    tempo_medio_por_prioridade = {}
    for prio in PRIORIDADES_VALIDAS:
        dados_prio = acumulador_prioridade[prio]
        tempo_medio_por_prioridade[prio] = _calcular_media_segura(
            dados_prio["soma_tempo"], dados_prio["quantidade"]
        )

    resultado = {
        "total_tarefas": total_tarefas,
        "total_concluidas": total_concluidas,
        "total_pendentes": total_pendentes,
        "tempo_medio_conclusao_horas": tempo_medio_conclusao_geral,
        "tempo_medio_conclusao_por_prioridade_horas": tempo_medio_por_prioridade,
        "taxa_atraso_percentual": taxa_atraso,
    }

    logger.info("Análise concluída com sucesso. Resultado gerado: %s", resultado)
    return resultado
