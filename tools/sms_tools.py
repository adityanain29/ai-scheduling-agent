# tools/sms_tools.py
# This tool handles sending SMS messages using the Twilio API.

from twilio.rest import Client
import sys
import os

class SMSTools:
    def __init__(self, account_sid, auth_token, twilio_phone_number):
        """
        Initializes the SMSTools with Twilio credentials.
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.twilio_phone_number = twilio_phone_number
        
        if self.account_sid and self.auth_token:
            self.client = Client(account_sid, auth_token)
        else:
            self.client = None

    def send_sms(self, to_phone_number: str, message_body: str) -> bool:
        """
        Sends an SMS message to the specified phone number.

        Args:
            to_phone_number: The recipient's phone number in E.164 format (e.g., +1234567890).
            message_body: The content of the SMS message.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        if not self.client:
            print("❌ Twilio client is not configured. Check your .env file. Cannot send SMS.")
            return False

        try:
            message = self.client.messages.create(
                body=message_body,
                from_=self.twilio_phone_number,
                to=to_phone_number
            )
            print(f"✅ SMS sent successfully to {to_phone_number} (SID: {message.sid})")
            return True
        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")
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

    print("🚀 Testing SMS Tools...")

    # IMPORTANT: To run this test, you must have your Twilio credentials
    # set in your .env file, and the recipient number must be verified in your
    # Twilio trial account.
    
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        print("\n⚠️ SKIPPING TEST: Please set all TWILIO variables in your .env file.")
    else:
        # Initialize the tool
        sms_tool = SMSTools(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            twilio_phone_number=settings.TWILIO_PHONE_NUMBER
        )

        # --- Test Case 1: Send a test SMS ---
        # Replace this with your personal, Twilio-verified phone number for testing.
        # It MUST be in E.164 format (e.g., +919876543210 for India).
        test_recipient_number = "+919610729029" # <-- CHANGE THIS to your number

        print(f"\n--- Test Case 1: Sending test SMS to {test_recipient_number} ---")
        
        success = sms_tool.send_sms(
            to_phone_number=test_recipient_number,
            message_body="This is a test message from the AI Medical Scheduler."
        )
        
        assert success is True
        print("✅ Test Case 1 Passed")

    print("\n🎉 SMS Tools tests completed successfully!")
