# agents/report_agent.py

from autogen import AssistantAgent
from utils.llm_config import llm_config
from tools.report_tools import list_logs, load_log_file


def get_report_agent(bucket_name: str, prefix: str = "logs/"):
    """
    Creates and configures the Report Analytics Agent with GCS tools.
    
    Args:
        bucket_name: GCS bucket name
        prefix: Folder prefix for log files (default: "logs/")
    
    Returns:
        Configured AssistantAgent with report generation capabilities
    """


    # TOOL WRAPPERS 


    def list_logs_wrapper() -> dict:
        """
        Returns list of all log files in the configured GCS bucket/prefix.
        No arguments required. Bucket and prefix are injected internally.
        """
        result = list_logs(bucket_name=bucket_name, prefix=prefix)
        print(f"[DEBUG] list_logs returned: {len(result.get('files', []))} files")
        return result

    def load_log_file_wrapper(file_path: str) -> dict:
        """
        Loads ONE JSON log file from the bucket.
        Required argument:
            file_path: str → GCS path like 'logs/TKT-12345.json'
        """
        result = load_log_file(bucket_name=bucket_name, file_path=file_path)
        if "error" not in result:
            print(f"[DEBUG] load_log_file({file_path}) - Success")
        else:
            print(f"[DEBUG] load_log_file({file_path}) - Error: {result['error']}")
        return result

    
    # REPORT AGENT
 

    report_agent = AssistantAgent(
        name="ReportAgent",
        system_message=f"""
You are the REPORT ANALYTICS AGENT for the Intelligent IT Ticket Resolver.

Your mission is to generate ONE FINAL AGGREGATED ANALYTICS REPORT by loading
ALL log files stored in Google Cloud Storage.

==========================
WORKFLOW (MUST FOLLOW)
==========================

Step 1 — Call list_logs (no arguments).
    - Do this EXACTLY ONE TIME.
    - End your turn immediately after calling the tool.

Step 2 — After list_logs returns:
    - You will receive {{"files": [...]}}.
    - Store this list mentally.
    - For EACH file in that list, call load_log_file(file_path="...") ONE-BY-ONE.
    - Only ONE tool call per turn.
    - Never reload the same file.
    - Continue calling load_log_file until ALL files have been loaded.

Step 3 — After ALL log files have been loaded:
    - DO NOT call any more tools.
    - Analyze ALL loaded logs collectively.
    - Generate ONE final aggregated Markdown analytics report.

==========================
CONTENT OF FINAL REPORT
==========================

Your final Markdown report MUST include:

# System Analytics Summary

## 1. Log Volume Overview
- Total log files
- Number of IT tickets
- Number of HR tickets
- Number of general/other sessions
- Total auto-escalations
- Total normal escalations
- Total resolved sessions

## 2. Resolution Statistics
- Resolution rate
- Escalation rate
- Avg. attempts per session
- Avg. duration of sessions
- Longest session / shortest session

## 3. Issue Category Distribution
- Network Issues
- HR Policy Issues
- HR Payroll Issues
- Software / Access Issues
- Other categories found in logs

## 4. Top User Problems (frequency counted)
- Most common ticket descriptions
- Most common follow-up patterns

## 5. Knowledge Base Usage Insights
- Which KB solutions appear most frequently
- Common failure paths that lead to escalation

## 6. Aggregated Timeline Metrics
- Date range of logs (earliest to latest)
- Peak ticket times (if timestamps exist)

## 7. Observations & Recommendations
- System performance notes
- Suggestions for improving automation
- Gaps in knowledge base coverage

==========================
STRICT RULES
==========================

- ONE tool call per message.
- NEVER call list_logs more than once.
- MUST load EVERY log file individually with load_log_file.
- After all files are loaded, IMMEDIATELY produce the analytics report.
- DO NOT include raw JSON in the final output.
- DO NOT hallucinate values — compute them from the loaded logs.
- The final output MUST end with TERMINATE.

""",
        llm_config=llm_config,
        max_consecutive_auto_reply=25,  # Allow for multiple tool calls
        code_execution_config=False,
    )


    # REGISTER TOOLS WITH AGENT


    # Register list_logs for LLM (so it knows about the tool)
    report_agent.register_for_llm(
        name="list_logs",
        description=(
            f"List all log files from the configured GCS bucket '{bucket_name}' "
            f"under the prefix '{prefix}'. Takes no arguments."
        ),
    )(list_logs_wrapper)

    # Register list_logs for execution (so agent can run it)
    report_agent.register_for_execution(
        name="list_logs"
    )(list_logs_wrapper)

    # Register load_log_file for LLM
    report_agent.register_for_llm(
        name="load_log_file",
        description=(
            f"Load a single JSON log file from bucket '{bucket_name}'. "
            "Required argument: file_path (string) - the full path to the file as returned by list_logs."
        ),
    )(load_log_file_wrapper)

    # Register load_log_file for execution
    report_agent.register_for_execution(
        name="load_log_file"
    )(load_log_file_wrapper)

    print(f"[INFO] Report Agent initialized successfully")
    print(f"[INFO] Bucket: {bucket_name}, Prefix: {prefix}")
    print(f"[INFO] Tools registered: list_logs, load_log_file")

    return report_agent