# AI-Medical-Appointment-Scheduling-Agent
A fully functional AI-powered medical appointment scheduling agent designed to address common inefficiencies in clinic operations. Built using a robust LangGraph and LangChain architecture, the agent guides users through a complete booking workflow in a conversational Streamlit application. It successfully implements all core requirements, including patient lookup with new/returning patient detection, smart scheduling with variable appointment durations, calendar conflict prevention, automated patient intake form distribution via email, and a multi-channel (SMS & Email) 3-tier reminder system with actionable prompts to confirm attendance and reduce patient no-shows.

## Configuration: Environment Setup Guide

### Prerequisites
- Python 3.11
- Git
- Windows PowerShell or a Unix-like shell
- Optional (for SMS): Twilio account and a verified phone number
- Optional (for email): SMTP account (e.g., Gmail with App Password)

### 1) Clone and create a virtual environment
```bash
# From a terminal (PowerShell on Windows)
git clone <your-repo-url> ai-scheduling-agent
cd ai-scheduling-agent

# Create and activate venv (Windows)
python -m venv .venv
.\.venv\Scripts\Activate

# Create and activate venv (macOS/Linux)
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Configure environment variables (.env)
Create a `.env` file in the project root with the following keys. Items marked required must be set for the feature to work.

```dotenv
# --- LLM via OpenRouter ---
OPENROUTER_API_KEY=your_openrouter_api_key_here           # required
OPENROUTER_MODEL_NAME=qwen/qwen3-8b:free                  # optional (default used if omitted)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1          # optional (default used if omitted)

# --- Twilio (SMS) ---
TWILIO_ACCOUNT_SID=your_twilio_sid                        # required for SMS
TWILIO_AUTH_TOKEN=your_twilio_auth_token                  # required for SMS
TWILIO_PHONE_NUMBER=+1234567890                           # required for SMS (E.164 format)

# --- SMTP Email ---
SMTP_SERVER=smtp.gmail.com                                # optional (default: smtp.gmail.com)
SMTP_PORT=587                                             # optional (default: 587)
EMAIL_ADDRESS=your_email@example.com                      # required for emails
EMAIL_PASSWORD=your_app_password_or_smtp_password         # required for emails

# --- Paths (defaults are fine; override only if relocating data) ---
# DATA_DIR=data
# PATIENTS_CSV_PATH=data/patients.csv
# DOCTOR_SCHEDULES_PATH=data/doctor_schedules.xlsx
# APPOINTMENTS_CSV_PATH=data/appointments.csv
# INTAKE_FORM_PATH=data/forms/New Patient Intake Form.pdf
# EXPORTS_DIR=exports
```

Notes:
- OpenRouter: Sign up and create an API key, then set `OPENROUTER_API_KEY`.
- Gmail: Use an App Password (not your regular password) if 2FA is enabled.
- Twilio: Trial accounts require verified recipient numbers and E.164 format.

### 4) Seed or verify data
The app expects these files to exist:
- `data/patients.csv`
- `data/appointments.csv` (can start empty; created by the app)
- `data/doctor_schedules.xlsx`
- `data/forms/New Patient Intake Form.pdf`

If missing, generate synthetic data:
```bash
python generate_data.py
```

### 5) Run the app
```bash
# From the project root with venv activated
streamlit run app.py
```
- Streamlit will start at `http://localhost:8501`.
- Provide your full name, DOB, preferred doctor, and location to begin.

### 6) Optional: Test integrations
- Email tool (manual test runner inside the file):
  - Ensure `EMAIL_ADDRESS` and `EMAIL_PASSWORD` are set.
  - Run:
    ```bash
    python tools/email_tools.py
    ```
- SMS tool (manual test runner inside the file):
  - Ensure all `TWILIO_*` variables are set and update the test recipient in `tools/sms_tools.py` (`test_recipient_number`).
  - Run:
    ```bash
    python tools/sms_tools.py
    ```

### 7) Linting and tests
```bash
# Lint
flake8

# Format
black .

# Run tests (if present)
pytest -q
```

### Troubleshooting
- Missing API keys: You’ll see friendly “configuration is missing in .env” messages; set the variables and retry.
- Windows build errors for optional packages: Update pip and try again; ensure you’re on Python 3.11.
- Email failures: Use an App Password for Gmail; check that less secure app access policies aren’t blocking SMTP.
- Twilio failures: Use verified numbers on trial accounts; confirm E.164 format and correct `TWILIO_PHONE_NUMBER`.
