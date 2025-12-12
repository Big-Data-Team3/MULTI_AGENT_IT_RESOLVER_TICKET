# agents/notification_agent.py

from autogen import AssistantAgent
from utils.llm_config import llm_config
from tools.send_email import escalate_ticket_with_email

def get_notification_agent():
    agent = AssistantAgent(
        name="NotificationAgent",
        system_message=(
            "You are an AI that generates escalation email bodies.\n\n"
            "The user will send you a JSON string with these keys:\n"
            "- ticket_id\n"
            "- issue\n"
            "- previous_solution\n"
            "- follow_up\n\n"
            "Your task:\n"
            "1. Parse the JSON.\n"
            "2. Create a clean, professional HTML email body.\n\n"
            "STRICT RULES:\n"
            "- Output ONLY the HTML body. No surrounding JSON, no markdown.\n"
            "- NEVER output None.\n"
            "- If any field is missing or empty, write 'Not provided'.\n\n"
            "HTML FORMAT TO USE:\n"
            "<p><strong>Ticket ID:</strong> ...</p>\n"
            "<p><strong>Issue:</strong> ...</p>\n"
            "<p><strong>Previous Solution:</strong> ...</p>\n"
            "<p><strong>Follow-up:</strong> ...</p>\n"
            "<p>Best regards,<br>AI Notification Agent</p>\n"
        ),
        llm_config=llm_config,
        code_execution_config={"use_docker": False},
    )

    # Register tool for LLM
    agent.register_for_llm(
        name="escalate_ticket_with_email",
        description="Sends an escalation email to the IT support team."
    )(escalate_ticket_with_email)

    # Register tool for execution
    agent.register_for_execution(
        name="escalate_ticket_with_email"
    )(escalate_ticket_with_email)

    return agent






# # agents/notification_agent.py

# from autogen import AssistantAgent
# from utils.llm_config import llm_config
# from tools.send_email import escalate_ticket_with_email


# def get_notification_agent():
#     agent = AssistantAgent(
#         name="NotificationAgent",
#         system_message=(
#             """When the user provides an unresolved issue, generate a professional, well-formatted email body summarizing the issue.
#                 Then call the tool using this structure:

#                 {
#                 \"tool\": \"escalate_ticket_with_email\",
#                 \"arguments\": {\"issue\": \"<full email body generated>\"}
#                 }

#                 Do not reply with anything else."""

#         ),
#         llm_config=llm_config,
#         code_execution_config={"use_docker": False},
#     )

#     # Register tool for LLM
#     agent.register_for_llm(
#         name="escalate_ticket_with_email",
#         description="Send an escalation email containing the unresolved support issue."
#     )(escalate_ticket_with_email)

#     # Register tool for actual execution
#     agent.register_for_execution(
#         name="escalate_ticket_with_email"
#     )(escalate_ticket_with_email)

#     return agent
