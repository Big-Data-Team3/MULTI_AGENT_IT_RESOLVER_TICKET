import os
from agents.report_agent import get_report_agent
from tools.report_tools import list_logs, load_log_file

BUCKET_NAME = "us-central1-it-agent-resolv-bd0fece4-bucket"
PREFIX = "logs/"


# INITIALIZE REPORT AGENT

print("\n=== INITIALIZING REPORT AGENT ===\n")
report_agent = get_report_agent(bucket_name=BUCKET_NAME, prefix=PREFIX)


# STEP 1 — Load list of logs (Python only)

print("\n=== LOADING LOG LIST FROM GCS ===")
log_list = list_logs(bucket_name=BUCKET_NAME, prefix=PREFIX)

files = log_list.get("files", [])
print(f"[INFO] Found {len(files)} log files.\n")


# STEP 2 — Load all logs locally

all_logs = []
print("=== LOADING ALL LOGS LOCALLY ===")

for f in files:
    print(f"  → Loading {f}")
    log_data = load_log_file(bucket_name=BUCKET_NAME, file_path=f)
    all_logs.append(log_data)

print("\n[INFO] Finished loading all logs.")
print(f"[INFO] Total logs loaded: {len(all_logs)}")


# STEP 3 — Prepare reports output directory

os.makedirs("reports", exist_ok=True)
print("\n=== GENERATING MARKDOWN REPORTS FOR EACH LOG ===\n")


# STEP 4 — Generate individual reports

def extract_output(response):
    """Extract final LLM content safely from AutoGen responses."""
    # Case 1: plain string
    if isinstance(response, str):
        return response

    # Case 2: dict-like
    if isinstance(response, dict):
        if "content" in response:
            return response["content"]
        if "reply" in response:
            return response["reply"]
        return str(response)

    # Case 3: AutoGen RunResponse (typical)
    if hasattr(response, "messages"):
        for msg in response.messages:
            # message objects may be dict or ChatMessage
            if hasattr(msg, "content"):
                return msg.content
            if isinstance(msg, dict) and "content" in msg:
                return msg["content"]

    # Case 4: maybe output_text
    if hasattr(response, "output_text"):
        return response.output_text

    # Fallback
    return str(response)


for log in all_logs:
    file_path = log["file_path"]
    content = log["content"]

    log_id = content.get("session_id") or file_path.replace("logs/", "").replace(".json", "")
    print(f" → Generating report for {log_id}")

    # Build LLM prompt for this ticket
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

    # LLM call (1 per log — no risk of 429)
    response = report_agent.generate_reply(
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract LLM output text
    report_markdown = extract_output(response)

    if not report_markdown:
        print(f"ERROR: Could not extract report for {log_id}")
        continue

    # Save report file
    out_path = f"reports/{log_id}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_markdown)

    print(f" ✓ Saved → {out_path}")

print("\n=== COMPLETED: ALL MARKDOWN REPORTS GENERATED ===")
print("Reports are available in the /reports directory.\n")

