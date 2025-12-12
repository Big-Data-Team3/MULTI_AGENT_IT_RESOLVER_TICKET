from tools.report_tools import list_logs, load_log_file

BUCKET = "us-central1-it-agent-resolv-bd0fece4-bucket"
PREFIX = "logs/"

print("\n=== TESTING list_logs ===")
files = list_logs(bucket_name=BUCKET, prefix=PREFIX)
print(files)

if "files" in files and len(files["files"]) > 0:
    first_file = files["files"][0]
    print("\n=== TESTING load_log_file ===")
    log = load_log_file(bucket_name=BUCKET, file_path=first_file)
    print(log)
else:
    print("\nNo log files found in bucket!")
