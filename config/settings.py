# config/settings.py
# This file loads environment variables and sets up application-wide configurations.

import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()

# --- LLM Configuration ---
# You are using OpenRouter, so we will configure it here.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Let's start with a capable and free model. You can change this to any model on OpenRouter.
# Recommended model: 'meta-llama/llama-3-8b-instruct'
# Other good options: 'mistralai/mistral-7b-instruct-v0.2', 'google/gemma-7b-it'
OPENROUTER_MODEL_NAME = "qwen/qwen3-8b:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# --- Twilio Configuration (for SMS) ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# --- Email Configuration (for SMTP) ---
# Note: You will need to configure these in your .env file for email to work.
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") # For Gmail, this should be an "App Password"

# --- Data File Paths ---
# Centralizing file paths makes them easier to manage.
DATA_DIR = "data"
PATIENTS_CSV_PATH = os.path.join(DATA_DIR, "patients.csv")
DOCTOR_SCHEDULES_PATH = os.path.join(DATA_DIR, "doctor_schedules.xlsx")
APPOINTMENTS_CSV_PATH = os.path.join(DATA_DIR, "appointments.csv")
INTAKE_FORM_PATH = os.path.join(DATA_DIR, "forms", "New Patient Intake Form.pdf")

# --- Application Settings ---
APPOINTMENT_DURATIONS = {
    "new_patient": 60,      # in minutes
    "returning_patient": 30 # in minutes
}

# --- Exports Directory ---
EXPORTS_DIR = "exports"
os.makedirs(EXPORTS_DIR, exist_ok=True) # Ensure the directory exists
