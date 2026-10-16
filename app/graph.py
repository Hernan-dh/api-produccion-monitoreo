from typing import TypedDict

from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from .hitl import request_approval
from .observability import trace_node


class AgentState(TypedDict, total=False):
    task: str
    critical: bool
    plan: str
    result: str


async def plan(state: AgentState) -> AgentState:
    return {"plan": await trace_node("planificador", state["task"])}


async def approval(state: AgentState) -> AgentState:
    if not state.get("critical", False):
        return {}
    accepted = request_approval(state["task"])
    if not accepted:
        return {"result": "Tarea crítica rechazada por la persona aprobadora."}
    return {}


async def execute(state: AgentState) -> AgentState:
    if state.get("result"):
        return {}
    result = await trace_node("ejecutor", state["task"])
    return {"result": f"Resultado completado. {result}"}


def build_graph(checkpointer: AsyncRedisSaver):
    workflow = StateGraph(AgentState)
    workflow.add_node("plan", plan)
    workflow.add_node("approval", approval)
    workflow.add_node("execute", execute)
    workflow.add_edge(START, "plan")
    workflow.add_edge("plan", "approval")
    workflow.add_edge("approval", "execute")
    workflow.add_edge("execute", END)
    return workflow.compile(checkpointer=checkpointer)


async def run_graph(redis_url: str, job_id: str, task: str, critical: bool, resume: bool = False):
    """Ejecuta o reanuda el mismo thread_id; Redis guarda los checkpoints."""
    async with AsyncRedisSaver.from_conn_string(redis_url) as saver:
        await saver.asetup()
        graph = build_graph(saver)
        config = {"configurable": {"thread_id": job_id}}
        payload = Command(resume=True) if resume else {"task": task, "critical": critical}
        return await graph.ainvoke(payload, config=config)
