"""Trazas opcionales a LangSmith; la API sigue funcionando sin credenciales."""
import os

from langsmith import traceable


def configure_observability() -> None:
    """Activa LangSmith cuando LANGSMITH_API_KEY está configurada."""
    if os.getenv("LANGSMITH_API_KEY"):
        os.environ.setdefault("LANGSMITH_TRACING", "true")
        os.environ.setdefault("LANGSMITH_PROJECT", "api-produccion-monitoreo")


@traceable(name="agent_node", run_type="chain")
async def trace_node(name: str, task: str) -> str:
    """Nodo instrumentado para que cada etapa aparezca en LangSmith."""
    return f"{name}: {task}"
