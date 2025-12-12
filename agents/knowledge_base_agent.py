from autogen import AssistantAgent
from utils.llm_config import llm_config
from tools.knowledge_base_tool import search_similar_solution


# agents/knowledge_base_agent.py

from autogen import AssistantAgent
from utils.llm_config import llm_config
from tools.knowledge_base_tool import search_similar_solution


def get_knowledge_base_agent():
    knowledge_agent = AssistantAgent(
        name="KnowledgeBaseAgent",
        system_message=(
            "You are a RAG retrieval agent. "
            "Your ONLY job is to call the 'search_similar_solution' tool using the query. "
            "Return ONLY the raw tool result. "
            "Do NOT summarize. "
            "Do NOT offer solutions. "
            "Do NOT answer the user's question. "
            "Do NOT output TERMINATE. "
            "Wait for the manager to forward your output."
        ),
        llm_config=llm_config,
        code_execution_config={"use_docker": False},
    )

    # Register tool for LLM and executor
    knowledge_agent.register_for_llm(
        name="search_similar_solution",
        description="Retrieve matching KB chunks using vector search."
    )(search_similar_solution)

    knowledge_agent.register_for_execution(
        name="search_similar_solution"
    )(search_similar_solution)

    return knowledge_agent
