# group_chat2.py — Option B with KB extraction + full logging + resolver instrumentation

import json
import logging
import autogen

# YOU WANT FULL ENGINE LOGS → do NOT disable any autogen logs
# Only ensure Python logger prints everything
logging.basicConfig(level=logging.INFO)

from autogen import UserProxyAgent, GroupChat, GroupChatManager

from agents.classifier_agent import get_classifier_agent
from agents.knowledge_base_agent import get_knowledge_base_agent
from agents.resolver_agent import get_resolver_agent
from utils.llm_config import llm_config


# ----------------------------------------------------------------------
# Load agents
# ----------------------------------------------------------------------
classifier_agent = get_classifier_agent()
kb_agent = get_knowledge_base_agent()
resolver_agent = get_resolver_agent()


# ----------------------------------------------------------------------
# User agent (NO auto replies)
# ----------------------------------------------------------------------
user_agent = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    code_execution_config={"use_docker": False},
)


# ----------------------------------------------------------------------
# GroupChat: Classifier + KB only
# max_round=4 so tool output appears
# ----------------------------------------------------------------------
def build_classifier_kb_chat():
    return GroupChat(
        agents=[user_agent, classifier_agent, kb_agent],
        messages=[],
        speaker_selection_method="round_robin",
        max_round=4  # MUST be 4 for tool output to appear!
    )


# ----------------------------------------------------------------------
# Classifier + KB Retrieval (with full tool output capture)
# ----------------------------------------------------------------------
def run_classifier_and_kb(query_text: str):
    print("\n\n========== CLASSIFIER + KB PIPELINE ==========")
    print("User Query:", query_text)

    groupchat = build_classifier_kb_chat()
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Trigger User → Classifier → KB → TOOL
    user_agent.initiate_chat(
        recipient=manager,
        message=query_text
    )

    classifier_json = {"category": "technical"}
    kb_output = ""

    for msg in groupchat.messages:
        if not isinstance(msg, dict):
            continue

        sender = msg.get("sender") or msg.get("name")

        print("\n[ENGINE MESSAGE]", msg)

        # -------- Classifier Output --------
        if sender == classifier_agent.name:
            print("\n[CLASSIFIER OUTPUT RAW]:", msg.get("content"))
            try:
                classifier_json = json.loads(msg.get("content"))
            except:
                classifier_json = {"category": "technical"}

        # -------- KB direct agent output --------
        if sender == kb_agent.name:
            print("\n[KB AGENT OUTPUT RAW]:", msg.get("content"))
            kb_output = msg.get("content", kb_output)

        # -------- KB TOOL OUTPUT (THIS IS THE REAL CHUNK) --------
        if msg.get("tool_name") == "search_similar_solution":
            print("\n[KB TOOL RESULT]:\n", msg.get("content"))
            kb_output = msg.get("content")

        if msg.get("name") == "search_similar_solution":
            print("\n[KB TOOL RESULT (name match)]:\n", msg.get("content"))
            kb_output = msg.get("content")

        if sender == "tool":
            print("\n[KB TOOL RESULT (sender=tool)]:\n", msg.get("content"))
            kb_output = msg.get("content")

    print("\n========== END CLASSIFIER + KB PIPELINE ==========\n")
    return classifier_json, kb_output


# ----------------------------------------------------------------------
# RESOLVER PIPELINE — FULL LOGGING
# ----------------------------------------------------------------------
def run_ticket_round(
    user_message: str,
    original_issue: str,
    previous_solution: str = "",
    follow_up: str = ""
):
    print("\n\n================= RESOLVER PIPELINE START =================")

    # Step 1: Classifier + KB
    classifier_json, kb_context = run_classifier_and_kb(
        follow_up if follow_up else user_message
    )

    issue_type = classifier_json.get("category", "technical")

    # Step 2: Build structured resolver payload
    resolver_payload = {
        "issue_text": original_issue,
        "previous_solution": previous_solution,
        "new_follow_up": follow_up,
        "issue_type": issue_type,
        "kb_context": kb_context,
    }

    print("\n\n[DEBUG] --- RESOLVER PAYLOAD SENT INTO RESOLVER ---")
    print(json.dumps(resolver_payload, indent=2))

    # Step 3: Call resolver agent directly
    resolver_reply = resolver_agent.generate_reply(
        messages=[{
            "role": "user",
            "content": json.dumps(resolver_payload)
        }]
    )

    final_answer = (
        resolver_reply.get("content", "")
        if isinstance(resolver_reply, dict)
        else str(resolver_reply)
    )

    print("\n[DEBUG] --- RESOLVER RAW OUTPUT ---")
    print(final_answer)
    print("\n================= RESOLVER PIPELINE END =================\n\n")

    return {
        "answer": final_answer,
        "previous_solution": final_answer,
        "kb_context": kb_context,
        "issue_type": issue_type,
    }


__all__ = ["run_ticket_round"]










