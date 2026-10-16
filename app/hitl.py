from langgraph.types import interrupt


def request_approval(task: str) -> bool:
    """Detiene el grafo y persiste el checkpoint hasta recibir Command(resume=...)."""
    return interrupt({"message": "La tarea es crítica y requiere aprobación humana.", "task": task})
