# tools/email_tools.py
# This tool handles sending emails with attachments, such as the patient intake form.

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import sys

class EmailTools:
    def __init__(self, smtp_server, port, sender_email, password):
        """
        Initializes the EmailTools with SMTP server configuration.
        """
        self.smtp_server = smtp_server
        self.port = port
        self.sender_email = sender_email
        self.password = password

    def send_form_email(self, recipient_email: str, patient_name: str, attachment_path: str) -> bool:
        """
        Sends the patient intake form to the specified recipient.
        """
        # ... (existing code for this method is unchanged) ...
        if not all([self.sender_email, self.password]):
            print("❌ Email configuration is missing in .env file. Cannot send email.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Your Upcoming Appointment & Patient Intake Form"

            body = f"Dear {patient_name},\n\nPlease find your patient intake form attached.\n\nBest regards,\nClinic Staff"
            msg.attach(MIMEText(body, 'plain'))

            with open(attachment_path, "rb") as attachment:
                part = MIMEApplication(attachment.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            
            print(f"✅ Intake form successfully sent to {recipient_email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send form email: {e}")
            return False

    def send_reminder_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """
        Sends a simple text-based reminder email.
        """
        if not all([self.sender_email, self.password]):
            print("❌ Email configuration is missing. Cannot send reminder email.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            
            print(f"✅ Reminder email successfully sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send reminder email: {e}")
            return False


# --- Example Usage & Testing ---
if __name__ == '__main__':
    # --- FIX FOR DIRECT EXECUTION ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    # --- END FIX ---

    # --- LOCAL IMPORTS ---
    from config import settings
    # --- END LOCAL IMPORTS ---

    print("🚀 Testing Email Tools...")
    
    # IMPORTANT: To run this test, you must have your EMAIL_ADDRESS and
    # EMAIL_PASSWORD (as an App Password) set in your .env file.
    
    if not settings.EMAIL_ADDRESS or not settings.EMAIL_PASSWORD:
        print("\n⚠️ SKIPPING TEST: Please set EMAIL_ADDRESS and EMAIL_PASSWORD in your .env file.")
    else:
        # Initialize the tool
        email_tool = EmailTools(
            smtp_server=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            sender_email=settings.EMAIL_ADDRESS,
            password=settings.EMAIL_PASSWORD
        )

        # --- Test Case 1: Send a test email ---
        print(f"\n--- Test Case 1: Sending test email to {settings.EMAIL_ADDRESS} ---")
        # For safety, the test will send the email to yourself.
        success = email_tool.send_form_email(
            recipient_email=settings.EMAIL_ADDRESS,
            patient_name="Test Patient",
            attachment_path=settings.INTAKE_FORM_PATH
        )
        
        assert success is True
        print("✅ Test Case 1 Passed")

    print("\n🎉 Email Tools tests completed successfully!")
