import streamlit as st
import json
import uuid
from datetime import datetime, UTC

from group_chat2 import run_ticket_round
from agents.notification_agent import get_notification_agent
from tools.send_email import escalate_ticket_with_email
from utils.chat_logger import save_chat_log, create_message
from utils.stdout_capture import capture_output



# INITIALIZATION & PAGE CONFIG


notification_agent = get_notification_agent()

st.set_page_config(page_title="TriAxis Support", page_icon="🤖", layout="wide")

st.sidebar.markdown(
    """
    <h2 style='margin-bottom:0px;'>🔧 TriAxis Support</h2>
    <p style='margin-top:4px; color:#6b6b6b;'>Unified IT • HR • Policy Assistant</p>
    """,
    unsafe_allow_html=True
)

page = st.sidebar.radio("Navigation", ["💬 Chat Assistant"])


# SAMPLE SUGGESTED QUERIES PANEL


sample_queries = {
    "🖥️ IT Support": [
        "Power BI says my dataset credentials are invalid.",
        "Azure API is returning blank responses in APIM.",
        "My Node app is consuming too much memory in Azure App Service.",
        "Blob upload fails with InvalidBlockList error.",
        "I’m getting 401 unauthorized while calling my API."
    ],

    "👥 HR (FLSA, Overtime, Classification)": [
        "Can my employer deduct the cost of uniforms from my paycheck?",
        "Am I exempt from overtime as a salaried manager?",
        "Does FLSA consider me an employee or an independent contractor?",
        "Are tipped employees entitled to minimum wage protections?",
        "Do first responders qualify for overtime exemptions?"
    ],

    "📘 HR – Policy & Leave (FMLA, H-2A, Records)": [
        "Am I eligible for FMLA if I worked 1,200 hours this year?",
        "Can I use FMLA leave to care for my adult child with a disability?",
        "What wage must H-2A agricultural workers be paid?",
        "What housing standards apply for H-2A visa workers?",
        "What payroll records is my employer legally required to keep?"
    ],
}

st.sidebar.markdown("### 💡 Sample Queries")

# Render categories and their sample questions
for category, questions in sample_queries.items():
    st.sidebar.markdown(f"**{category}**")
    
    formatted_list = "<ul style='margin-top:4px; margin-bottom:14px; padding-left:18px;'>"
    for q in questions:
        formatted_list += f"<li style='font-size:13.5px; color:#444;'>{q}</li>"
    formatted_list += "</ul>"

    st.sidebar.markdown(formatted_list, unsafe_allow_html=True)

# CSS


chat_css = """
<style>
body { background-color: #f5f7fa; }

.chat-container { max-width: 900px; margin: auto; }

.msg {
    padding: 14px 18px;
    margin: 12px 0;
    border-radius: 16px;
    max-width: 75%;
    font-size: 15px;
    line-height: 1.5;
    animation: fadeIn 0.25s ease-in-out;
}

.msg.user { background-color: #e7f0ff; border: 1px solid #c9ddff; margin-left: auto; }
.msg.ai { background-color: #fff; border: 1px solid #e2e2e2; margin-right: auto; }

textarea { border-radius: 10px !important; border: 1px solid #ccc !important; }

.agent-log {
    background: #f0f0f0;
    padding: 10px;
    border-radius: 12px;
    margin: 10px 0;
    white-space: pre-wrap;
    font-family: monospace;
    max-height: 260px;
    overflow-y: auto;
    font-size: 13px;
}

.ticket-header {
    background: #f0f8ff;
    padding: 10px 14px;
    border-radius: 12px;
    margin-bottom: 12px;
    border: 1px solid #d1eaff;
}

.status-pill {
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12px;
}

.status-pending { background-color: #fff4cc; color: #8a6d00; }
.status-escalated { background-color: #ffd7d7; color: #a30000; }
.status-resolved { background-color: #d4f6da; color: #1e7e34; }
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

right_panel_css = """
<style>

#right-sample-panel {
    position: fixed;
    top: 80px;
    right: 0px;
    width: 260px;
    height: 85%;
    padding: 12px;
    background-color: #ffffff;
    border-left: 1px solid #e5e5e5;
    overflow-y: auto;
    border-radius: 8px 0 0 8px;
    box-shadow: -3px 0px 6px rgba(0,0,0,0.08);
    z-index: 9999;
}

#right-sample-toggle {
    position: fixed;
    top: 80px;
    right: 260px;
    background-color: #ffffff;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #e5e5e5;
    cursor: pointer;
    z-index: 9999;
}

</style>
"""

st.markdown(right_panel_css, unsafe_allow_html=True)


# SESSION STATE DEFAULTS


defaults = {
    "history": [],
    "final_response": None,
    "awaiting_followup": False,
    "issue_input": "",
    "followup_input": "",
    "followup_attempts": 0,
    "max_attempts": 5,
    "clear_issue": False,
    "clear_followup": False,
    "chat_log_messages": [],
    "session_start": "",
    "force_escalate": False,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.session_start:
    st.session_state.session_start = datetime.now(UTC).isoformat()



# AUTOMATIC ESCALATION HANDLER 


def perform_auto_escalation():
    """Runs an escalation without showing UI (fixes rendering issue)."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

    escalation_payload = {
        "ticket_id": ticket_id,
        "issue": st.session_state.issue_input,
        "previous_solution": st.session_state.final_response,
        "follow_up": st.session_state.followup_input or "Not provided",
        "attempts_used": st.session_state.followup_attempts,
    }

    st.session_state.chat_log_messages.append(
        create_message("system", f"Auto escalation triggered for {ticket_id}")
    )

    notif_reply = notification_agent.generate_reply(
        messages=[{"role": "user", "content": json.dumps(escalation_payload)}]
    )

    st.session_state.chat_log_messages.append(
        create_message("NotificationAgent", str(notif_reply))
    )

    email_body = notif_reply["content"] if isinstance(notif_reply, dict) else str(notif_reply)
    escalate_ticket_with_email(email_body=email_body)

    save_chat_log(ticket_id, {
        "session_id": ticket_id,
        "status": "auto_escalated",
        "start_time": st.session_state.session_start,
        "end_time": datetime.now(UTC).isoformat(),
        "messages": st.session_state.chat_log_messages,
        "payload": escalation_payload,
        "email_body": email_body,
    })

    # Reset entire conversation
    st.session_state.clear_issue = True
    st.session_state.clear_followup = True
    st.session_state.issue_input = ""
    st.session_state.followup_input = ""
    st.session_state.history = []
    st.session_state.chat_log_messages = []
    st.session_state.final_response = None
    st.session_state.awaiting_followup = False
    st.session_state.followup_attempts = 0
    st.session_state.session_start = datetime.now(UTC).isoformat()
    st.session_state.force_escalate = False

    st.rerun()



#               EXECUTE AUTO ESCALATION FIRST


if st.session_state.force_escalate:
    perform_auto_escalation()
    st.stop()



# CHAT ASSISTANT UI

if "show_sample_panel" not in st.session_state:
    st.session_state.show_sample_panel = False


if page == "💬 Chat Assistant":

    # Clear fields if flagged
    if st.session_state.clear_issue:
        st.session_state.issue_input = ""
        st.session_state.clear_issue = False
    if st.session_state.clear_followup:
        st.session_state.followup_input = ""
        st.session_state.clear_followup = False

    # ---------------- HEADER ----------------
    st.markdown(
        """
        <div style='text-align:center;'>
            <h1 style='font-size:40px;'>🤖 TriAxis Support</h1>
            <p style='font-size:18px; color:#555;'>Unified IT, HR & Policy Support System</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # ---------------- ISSUE INPUT ----------------
    st.markdown("<div style='max-width:900px; margin:auto;'>", unsafe_allow_html=True)
    col_in, col_btn = st.columns([4, 1])

    with col_in:
        issue_text = st.text_area(
            "Issue Input",
            value=st.session_state.issue_input,
            key="issue_input_box",
            height=120,
            label_visibility="collapsed",
            placeholder="Eg. VPN not connecting, payroll question…"
        )

    with col_btn:
        resolve_clicked = st.button("🚀 Resolve Issue", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- HANDLE PRIMARY ISSUE ----------------
    if resolve_clicked:
        if not issue_text.strip():
            st.warning("Please describe your issue.")
        else:
            st.session_state.issue_input = issue_text
            st.session_state.history.append({"role": "user", "content": issue_text})
            st.session_state.chat_log_messages.append(create_message("user", issue_text))

            result, logs = capture_output(
                run_ticket_round,
                user_message=issue_text,
                original_issue=issue_text,
                previous_solution="",
                follow_up=""
            )

            st.session_state.chat_log_messages.append(create_message("agent_pipeline", logs))

            answer = result["answer"]
            st.session_state.history.append({"role": "assistant", "content": answer})
            st.session_state.chat_log_messages.append(create_message("assistant", answer))

            st.session_state.final_response = answer
            st.session_state.awaiting_followup = False
            st.session_state.followup_attempts = 0

            st.rerun()

    # ---------------- SHOW TICKET STATUS ----------------
    if st.session_state.final_response:
        st.markdown(
            """
            <div class='ticket-header'>
                <strong>Ticket Status:</strong>
                <span class='status-pill status-pending'>Waiting for your feedback</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------------- DISPLAY CONVERSATION ----------------
    st.markdown("<h3>💬 Conversation</h3>", unsafe_allow_html=True)
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    for msg in st.session_state.history:
        css = "user" if msg["role"] == "user" else "ai"
        label = "🧑 User" if msg["role"] == "user" else "🤖 TriAxis AI"
        st.markdown(
            f'<div class="msg {css}"><strong>{label}:</strong> {msg["content"]}</div>',
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

   
    #                FEEDBACK YES / NO BUTTONS
    
    if st.session_state.final_response and not st.session_state.awaiting_followup:

        st.markdown("### Was this response helpful?")
        col1, col2 = st.columns(2)

        # ---- YES RESOLVED ----
        with col1:
            if st.button("✅ Yes, issue resolved"):
                session_id = f"session-{datetime.now(UTC).timestamp()}"
                save_chat_log(session_id, {
                    "session_id": session_id,
                    "status": "resolved",
                    "start_time": st.session_state.session_start,
                    "end_time": datetime.now(UTC).isoformat(),
                    "messages": st.session_state.chat_log_messages,
                })

                st.session_state.clear_issue = True
                st.session_state.clear_followup = True
                st.session_state.history = []
                st.session_state.chat_log_messages = []
                st.session_state.final_response = None
                st.session_state.awaiting_followup = False
                st.session_state.followup_attempts = 0
                st.session_state.session_start = datetime.now(UTC).isoformat()

                st.rerun()

        # ---- NO, NEED FOLLOW-UP ----
        with col2:
            if st.button("❌ No, not helpful"):
                st.session_state.awaiting_followup = True
                st.rerun()


    #                    FOLLOW-UP MODE

    if st.session_state.awaiting_followup:

        remaining = st.session_state.max_attempts - st.session_state.followup_attempts
        st.markdown("### Follow-up clarification")
        st.info(f"🔁 Follow-up attempts left: **{remaining} / {st.session_state.max_attempts}**")

        # if out of attempts → escalate immediately
        if remaining <= 0:
            st.warning("⚠️ Maximum refinement attempts reached. Escalating automatically…")
            st.session_state.force_escalate = True
            st.rerun()

        follow_text = st.text_area(
            "Follow-up Input",
            value=st.session_state.followup_input,
            key="followup_input_box",
            height=120,
            label_visibility="collapsed"
        )

        colA, colB = st.columns(2)

        # ---- REFINE SOLUTION ----
        with colA:
            if st.button("🔄 Refine Solution"):

                if not follow_text.strip():
                    st.warning("Please enter clarification.")
                    st.stop()

                st.session_state.followup_attempts += 1
                st.session_state.followup_input = follow_text

                # log message
                st.session_state.history.append({"role": "user", "content": follow_text})
                st.session_state.chat_log_messages.append(create_message("user", follow_text))

                combined_msg = (
                    f"User says previous solution did not work.\n"
                    f"Original Issue: {st.session_state.issue_input}\n"
                    f"Previous Solution: {st.session_state.final_response}\n"
                    f"Follow-up: {follow_text}"
                )

                result, logs = capture_output(
                    run_ticket_round,
                    user_message=combined_msg,
                    original_issue=st.session_state.issue_input,
                    previous_solution=st.session_state.final_response,
                    follow_up=follow_text
                )

                st.session_state.chat_log_messages.append(create_message("agent_pipeline", logs))

                reply = result["answer"]
                st.session_state.final_response = reply

                st.session_state.history.append({"role": "assistant", "content": reply})
                st.session_state.chat_log_messages.append(create_message("assistant", reply))

                st.session_state.clear_followup = True
                st.session_state.awaiting_followup = False

                st.rerun()

        # ---- ESCALATE BUTTON ----
        with colB:
            if st.button("🚨 Escalate to Human Support"):
                st.session_state.force_escalate = True
                st.rerun()

    
    # INTERNAL PIPELINE LOGS
    
    with st.expander("🔍 Internal System Diagnostics (Agent Pipeline Logs)"):
        logs = [x for x in st.session_state.chat_log_messages if x["role"] == "agent_pipeline"]
        if not logs:
            st.caption("No logs yet.")
        else:
            for entry in logs:
                st.markdown(f"<div class='agent-log'>{entry['content']}</div>", unsafe_allow_html=True)




