import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Replace these with your actual SMTP credentials
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
ESCALATION_EMAIL = os.getenv("ESCALATION_EMAIL") # Use App Password for Gmail

def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        print("📧 Preparing to send email...")
        print("From:", SENDER_EMAIL)
        print("To:", to_email)
        print("SMTP Server:", SMTP_SERVER)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

        print("📧 Email successfully sent!")
        return True

    except Exception as e:
        print("❌ Error sending email:", str(e))
        return False

def escalate_ticket_with_email(email_body: str) -> dict:
    subject = "Escalation Required: Unresolved IT Support Ticket"

    html_wrapper = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.5;">
        <h2>IT Ticket Escalation</h2>

        {email_body}

        <br><br>
        <p>Best regards,<br>
        <strong>AI Notification Agent</strong></p>
    </body>
    </html>
    """

    success = send_email(
    to_email=ESCALATION_EMAIL,
    subject=subject,
    body=html_wrapper
    )

    return {
        "content": "📧 Escalation email sent successfully." if success else "⚠️ Failed to send escalation email."
    }
    