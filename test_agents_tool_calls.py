from agents.report_agent import get_report_agent

BUCKET = "us-central1-it-agent-resolv-bd0fece4-bucket"
PREFIX = "logs/"

agent = get_report_agent(bucket_name=BUCKET, prefix=PREFIX)

print("\n=== REPORT AGENT SYSTEM MESSAGE ===\n")
print(agent.system_message)

print("\n=== RUNNING REPORT AGENT RAW ===\n")

response = agent.run(
    "Begin generating the report. First, call the list_logs tool to retrieve all log files.",
    stream=False,
)



print("\n=== RAW RESPONSE OBJECT ===")
print(response)

print("\n=== MESSAGES (IF ANY) ===")
if hasattr(response, "messages"):
    for m in response.messages:
        print(m)
else:
    print("<< NO MESSAGES >>")

print("\n=== FINAL CONTENT ===")
print(getattr(response, "content", "<< NO CONTENT >>"))

print("\n=== REGISTERED TOOLS ===")
print(agent._tools)
