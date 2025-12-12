import streamlit as st
import os
from agents.report_agent import get_report_agent
from tools.report_tools import list_logs, load_log_file


# CONFIG

BUCKET_NAME = "us-central1-it-agent-resolv-bd0fece4-bucket"
PREFIX = "logs/"


# STREAMLIT PAGE SETUP

st.set_page_config(page_title="Ticket Report Generator", layout="wide")

st.title("📊 IT Ticket Report Generator")
st.write("Select a log file from the dropdown and generate a detailed markdown report.")

import streamlit as st
import os
from agents.report_agent import get_report_agent
from tools.report_tools import list_logs, load_log_file

BUCKET_NAME = "us-central1-it-agent-resolv-bd0fece4-bucket"
PREFIX = "logs/"


# Initialize Agent

@st.cache_resource
def load_agent():
    return get_report_agent(bucket_name=BUCKET_NAME, prefix=PREFIX)

report_agent = load_agent()


# Always fetch updated log list

def get_log_list():
    log_list = list_logs(bucket_name=BUCKET_NAME, prefix=PREFIX)
    return log_list.get("files", [])

# Add refresh button
if st.button("🔄 Refresh Log List"):
    st.session_state["log_files"] = get_log_list()

files = st.session_state.get("log_files", get_log_list())

if not files:
    st.error("No log files found in GCS bucket.")
    st.stop()

selected_file = st.selectbox("Select log file", files)


# Load log content when selected

def load_selected_log(file_path):
    return load_log_file(bucket_name=BUCKET_NAME, file_path=file_path)



# Generate the report (LLM)

def extract_output(response):
    """Extract final LLM content from Autogen response."""
    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        return response.get("content") or response.get("reply") or str(response)

    if hasattr(response, "messages"):
        for msg in response.messages:
            if hasattr(msg, "content"):
                return msg.content
            if isinstance(msg, dict) and "content" in msg:
                return msg["content"]

    if hasattr(response, "output_text"):
        return response.output_text

    return str(response)


# UI BUTTON AND OUTPUT

if st.button("Generate Report"):
    with st.spinner("Processing ticket... Please wait."):

        # Load selected log from GCS
        log = load_selected_log(selected_file)
        content = log["content"]
        log_id = content.get("session_id") or selected_file.replace("logs/", "").replace(".json", "")

        # Build prompt
        prompt = f"""
You are the analytics engine.

Generate a **detailed, structured Markdown report** for this log:
- Ticket/session ID
- Start/end time
- Duration
- Status (resolved / escalated)
- Issue text
- Number of attempts
- Auto-escalation detection
- Conversation timeline summary
- KB search results used
- Resolver outputs summary
- User sentiment / behavior summary
- Root cause classification
- Recommendations to improve system performance
- Recommendations for IT/helpdesk team
- Any anomalies in pipeline execution

End the report with this exact text: TERMINATE

Here is the full log content:
{content}
"""

        # LLM response
        response = report_agent.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )

        report_markdown = extract_output(response)

        if not report_markdown:
            st.error("Could not extract report content.")
        else:
            st.success("Report successfully generated!")
            st.markdown(report_markdown)

            # Download button
            st.download_button(
                label="⬇️ Download Markdown Report",
                data=report_markdown,
                file_name=f"{log_id}.md",
                mime="text/markdown"
            )
