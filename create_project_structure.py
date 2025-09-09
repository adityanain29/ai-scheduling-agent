import os

# Create the complete project directory structure
directories = [
    "agents",
    "tools", 
    "data",
    "data/forms",
    "config",
    "tests",
    "utils",
    "exports"
]

files_to_create = [
    "agents/__init__.py",
    "agents/greeting_agent.py",
    "agents/patient_lookup_agent.py", 
    "agents/scheduling_agent.py",
    "agents/insurance_agent.py",
    "agents/reminder_agent.py",
    "tools/__init__.py",
    "tools/database_tools.py",
    "tools/calendar_tools.py",
    "tools/email_tools.py",
    "tools/sms_tools.py",
    "tools/export_tools.py",
    "config/__init__.py",
    "config/settings.py",
    "config/prompts.py",
    "utils/__init__.py",
    "utils/validators.py",
    "utils/helpers.py",
    "main_graph.py",
    "app.py",
    "generate_data.py",
    "README.md"
]

def create_project_structure():
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

    # Create files
    for file_path in files_to_create:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(f"# {file_path}\n# TODO: Implement\n")
            print(f"📄 Created file: {file_path}")

if __name__ == "__main__":
    create_project_structure()
    print("\n🎉 Project structure created successfully!")