from ai_investmate_be.db import get_latest_knowledge_graph

from fastapi import APIRouter


router = APIRouter()


@router.get("/kg")
async def knowledge_graph() -> dict:
    knowledge_graph_data = get_latest_knowledge_graph()
    print(f"knowledge_graph_data: {knowledge_graph_data}")
    knowledge_graph_data.pop("created_on", None)
    return knowledge_graph_data