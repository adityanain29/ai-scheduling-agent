# main_graph.py
# This file defines the core state machine and workflow, now with extended information collection and confirmation.

from typing import TypedDict, List, Annotated, Literal
import operator
import sys
import os
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# --- FIX FOR DIRECT EXECUTION ---
# This ensures we can run this file directly for testing, and it can find the other modules.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
# --- END FIX ---

# Import configurations, prompts, agents, and tools
from config import settings, prompts
from tools.database_tools import PatientDB
from tools.calendar_tools import CalendarTools
from tools.export_tools import ExportTools
from tools.email_tools import EmailTools
from agents.greeting_agent import (
    create_greeting_chain, 
    normalize_and_validate_patient_info, 
    PatientInfo,
    format_patient_info_for_confirmation,
    get_missing_info_message,
    is_patient_info_complete
)
from agents.patient_lookup_agent import lookup_patient, PatientNotFoundError
from agents.scheduling_agent import create_selection_parser_chain
from agents.insurance_agent import create_insurance_parser_chain, normalize_and_validate_insurance_info

# --- 1. Define the State for the Graph ---
class AgentState(TypedDict, total=False):
    """
    Represents the state of our conversation.
    `total=False` means keys are optional.
    """
    messages: Annotated[List[dict], operator.add]
    patient_info: PatientInfo | None 
    patient_id: str | None
    is_new_patient: bool | None
    available_slots: List[str] | None
    chosen_slot: str | None
    appointment_id: str | None # To store the final ID
    patient_email: str | None # To store patient's email
    conversation_stage: str

# --- 2. Initialize Models and Tools ---
llm = ChatOpenAI(
    model=settings.OPENROUTER_MODEL_NAME,
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
    temperature=0,
    streaming=True,
)

patient_db = PatientDB(filepath=settings.PATIENTS_CSV_PATH)
calendar_tool = CalendarTools(
    schedules_filepath=settings.DOCTOR_SCHEDULES_PATH,
    appointments_filepath=settings.APPOINTMENTS_CSV_PATH,
    appointment_durations=settings.APPOINTMENT_DURATIONS
)
export_tool = ExportTools(
    appointments_filepath=settings.APPOINTMENTS_CSV_PATH,
    patients_filepath=settings.PATIENTS_CSV_PATH,
    exports_dir=settings.EXPORTS_DIR
)
greeting_agent_chain = create_greeting_chain(llm, prompts.MASTER_PROMPT)
selection_parser_chain = create_selection_parser_chain(llm, prompts.MASTER_PROMPT)
insurance_parser_chain = create_insurance_parser_chain(llm, prompts.MASTER_PROMPT)

# --- 3. Define the Nodes with Extended Information Collection ---

def format_history(messages: List[dict]) -> str:
    """Helper function to format message history for prompts."""
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

def greeting_node(state: AgentState):
    """
    Initial greeting node that collects patient information and asks for missing details.
    """
    print("---NODE: GREETING---")
    
    # If this is the very first message, greet the user and ask for all information
    if len(state['messages']) == 1 and not state.get('patient_info'):
        state['messages'].append({
            "role": "assistant", 
            "content": "Hello! I'm here to help you schedule a medical appointment. To get started, please provide me with the following information:\n\n• Your full name\n• Your date of birth\n• Your preferred doctor\n• Your preferred location\n\nYou can provide all this information at once or we can go through it step by step."
        })
        state['conversation_stage'] = 'greeting'
        return state
    
    # Parse the conversation to extract patient information
    history = format_history(state['messages'])
    raw_info = greeting_agent_chain.invoke({"conversation_history": history})
    patient_info = normalize_and_validate_patient_info(raw_info)
    
    # Update the state with the current patient info
    if state.get('patient_info'):
        # Merge with existing info, prioritizing new non-null values
        existing_info = state['patient_info']
        updated_info = PatientInfo(
            full_name=patient_info.full_name or existing_info.full_name,
            date_of_birth=patient_info.date_of_birth or existing_info.date_of_birth,
            preferred_doctor=patient_info.preferred_doctor or existing_info.preferred_doctor,
            preferred_location=patient_info.preferred_location or existing_info.preferred_location
        )
        state['patient_info'] = updated_info
    else:
        state['patient_info'] = patient_info
    
    # Check if all information is collected
    if is_patient_info_complete(state['patient_info']):
        state['conversation_stage'] = 'information_confirmation'
    else:
        missing_msg = get_missing_info_message(state['patient_info'])
        state['messages'].append({"role": "assistant", "content": missing_msg})
        state['conversation_stage'] = 'greeting'
    
    return state

def information_confirmation_node(state: AgentState):
    """
    Node that displays collected information and asks for user confirmation.
    """
    print("---NODE: INFORMATION CONFIRMATION---")
    
    # Check if this is a confirmation response
    last_user_message = None
    for msg in reversed(state['messages']):
        if msg['role'] == 'user':
            last_user_message = msg['content'].lower().strip()
            break
    
    # If user is confirming or correcting
    if last_user_message and any(word in last_user_message for word in ['yes', 'correct', 'right', 'confirm', 'looks good']):
        # User confirmed, move to patient lookup
        state['conversation_stage'] = 'patient_lookup'
        return state
    elif last_user_message and any(word in last_user_message for word in ['no', 'wrong', 'incorrect', 'change', 'update']):
        # User wants to make changes, go back to greeting
        state['messages'].append({
            "role": "assistant",
            "content": "No problem! Please tell me what information you'd like to update, and I'll make the changes."
        })
        state['conversation_stage'] = 'greeting'
        return state
    
    # Display information for confirmation
    formatted_info = format_patient_info_for_confirmation(state['patient_info'])
    state['messages'].append({
        "role": "assistant",
        "content": f"Thank you! Let me confirm the information you've provided:\n\n{formatted_info}\n\nIs this information correct? Please say 'yes' to confirm or 'no' if you need to make any changes."
    })
    state['conversation_stage'] = 'information_confirmation'
    
    return state

def patient_lookup_node(state: AgentState):
    print("---NODE: PATIENT LOOKUP---")
    patient_info = state['patient_info']
    try:
        lookup_result = lookup_patient(
            patient_name=patient_info.full_name,
            patient_dob=patient_info.date_of_birth,
            db_tool=patient_db
        )
        state.update(lookup_result)
        patient_type = "new" if lookup_result['is_new_patient'] else "returning"
        state['messages'].append({
            "role": "assistant",
            "content": f"Perfect! I've found your file. You are a {patient_type} patient. Now let me check available appointment slots for Dr. {patient_info.preferred_doctor} at {patient_info.preferred_location}."
        })
        state['conversation_stage'] = 'find_slots'
    except PatientNotFoundError:
        state.update({'patient_id': "NEW_PATIENT", 'is_new_patient': True})
        state['messages'].append({
            "role": "assistant",
            "content": f"Thank you! It seems this is your first time with us. Welcome! Let me check available appointment slots for Dr. {patient_info.preferred_doctor} at {patient_info.preferred_location}."
        })
        state['conversation_stage'] = 'find_slots'
    return state

def find_slots_node(state: AgentState):
    print("---NODE: FIND SLOTS---")
    is_new = state.get('is_new_patient', True)
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    
    calendar_tool._load_booked_slots()
    available_slots = calendar_tool.find_available_slots(is_new, start_date, end_date)
    state['available_slots'] = available_slots
    
    if available_slots:
        slots_str = "\n".join([f"{i+1}. {s}" for i, s in enumerate(available_slots[:5])])
        duration = "60 minutes" if is_new else "30 minutes"
        patient_info = state['patient_info']
        state['messages'].append({
            "role": "assistant",
            "content": f"Great! Here are some available {duration} appointment slots with Dr. {patient_info.preferred_doctor} at {patient_info.preferred_location}:\n\n{slots_str}\n\nWhich slot would you prefer? Please select by number or tell me which one works best for you."
        })
        state['conversation_stage'] = 'selection_parser'
    else:
        patient_info = state['patient_info']
        state['messages'].append({
            "role": "assistant",
            "content": f"I'm sorry, but I couldn't find any available slots with Dr. {patient_info.preferred_doctor} at {patient_info.preferred_location} in the next two weeks. Would you like me to check with a different doctor or location?"
        })
        state['conversation_stage'] = 'completed'
    return state

def selection_parser_node(state: AgentState):
    print("---NODE: SELECTION PARSER---")
    
    # Get the latest user message (the user's selection)
    last_user_message = None
    for msg in reversed(state['messages']):
        if msg['role'] == 'user':
            last_user_message = msg['content']
            break
    
    # Format available slots for the prompt
    slots_str = "\n".join([f"{i+1}. {s}" for i, s in enumerate(state['available_slots'])])
    
    # Invoke the selection parser with expected variables
    result = selection_parser_chain.invoke({
        "available_slots": slots_str,
        "user_message": last_user_message or ""
    })
    
    # Extract possible keys
    slot_number = (
        result.get('slotNumber') or 
        result.get('slot_number') or 
        result.get('number')
    )
    selected_slot = (
        result.get('selectedSlot') or 
        result.get('selected_slot') or 
        result.get('slot')
    )
    
    # If we have a valid slot number, map it to the actual slot
    if isinstance(slot_number, int) and 1 <= slot_number <= len(state['available_slots']):
        state['chosen_slot'] = state['available_slots'][slot_number - 1]
        state['conversation_stage'] = 'confirmation'
        return state
    
    # Try to use selected slot text if unambiguous
    if selected_slot and selected_slot != "AMBIGUOUS":
        for i, slot in enumerate(state['available_slots']):
            if selected_slot in slot or slot in selected_slot:
                state['chosen_slot'] = slot
                state['conversation_stage'] = 'confirmation'
                return state
    
    # If ambiguous, ask user to clarify
    state['messages'].append({
        "role": "assistant",
        "content": "I'm sorry, I couldn't determine which slot you prefer. Please reply with the number of your chosen option (e.g., '1', 'Option 2')."
    })
    state['conversation_stage'] = 'find_slots'
    return state

def confirmation_node(state: AgentState):
    print("---NODE: CONFIRMATION---")
    try:
        appointment_id = export_tool.book_appointment(
            patient_id=state['patient_id'],
            chosen_slot=state['chosen_slot'],
            is_new_patient=state['is_new_patient']
        )
        state['appointment_id'] = appointment_id
        patient_info = state['patient_info']
        state['messages'].append({
            "role": "assistant",
            "content": f"Excellent! Your appointment is confirmed with ID **{appointment_id}** for:\n\n**{state['chosen_slot']}**\n**Doctor:** {patient_info.preferred_doctor}\n**Location:** {patient_info.preferred_location}\n\nWhat is a good email address to send the intake form to?"
        })
        state['conversation_stage'] = 'email_collection'
    except Exception as e:
        print(f"ERROR during booking: {e}")
        state['messages'].append({
            "role": "assistant",
            "content": "I'm sorry, there was an error while trying to book your appointment. Please try again."
        })
        state['conversation_stage'] = 'find_slots'
    return state

def email_collection_node(state: AgentState):
    print("---NODE: EMAIL COLLECTION---")
    history = format_history(state['messages'])
    raw_info = insurance_parser_chain.invoke({"conversation_history": history})
    insurance_info = normalize_and_validate_insurance_info(raw_info)
    
    if insurance_info.patient_email:
        state['patient_email'] = insurance_info.patient_email
        # Initialize and use the email tool
        email_tool = EmailTools(settings.SMTP_SERVER, settings.SMTP_PORT, settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
        email_tool.send_form_email(
            recipient_email=insurance_info.patient_email,
            patient_name=state['patient_info'].full_name,
            attachment_path=settings.INTAKE_FORM_PATH
        )
        patient_info = state['patient_info']
        state['messages'].append({
            "role": "assistant", 
            "content": f"Perfect! I've sent the intake form to {insurance_info.patient_email}. Your appointment is all set!\n\n**Appointment Summary:**\n- **ID:** {state['appointment_id']}\n- **Patient:** {patient_info.full_name}\n- **Date/Time:** {state['chosen_slot']}\n- **Doctor:** {patient_info.preferred_doctor}\n- **Location:** {patient_info.preferred_location}\n\nIs there anything else I can help you with?"
        })
        state['conversation_stage'] = 'completed'
    else:
        state['messages'].append({"role": "assistant", "content": "I didn't catch a valid email address. Could you please provide it so I can send the forms?"})
        state['conversation_stage'] = 'email_collection'
    return state

# --- 4. Define the Main Router ---

def route_conversation(state: AgentState) -> str:
    """
    Routes the conversation based on current stage and last message.
    """
    print(f"---ROUTER: Current stage = {state.get('conversation_stage', 'greeting')}---")
    
    stage = state.get('conversation_stage', 'greeting')
    
    # Special handling: if we're moving to find_slots, don't wait for user input
    if stage == 'find_slots':
        return 'find_slots'
    
    # For all other stages, only proceed if the last message is from user
    if state.get('messages') and state['messages'][-1]['role'] == 'assistant':
        return END
    
    return stage

# --- 5. Build the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("greeting", greeting_node)
workflow.add_node("information_confirmation", information_confirmation_node)
workflow.add_node("patient_lookup", patient_lookup_node)
workflow.add_node("find_slots", find_slots_node)
workflow.add_node("selection_parser", selection_parser_node)
workflow.add_node("confirmation", confirmation_node)
workflow.add_node("email_collection", email_collection_node)

# This is the routing map that will be used for all conditional edges.
router_map = {
    "greeting": "greeting",
    "information_confirmation": "information_confirmation",
    "patient_lookup": "patient_lookup",
    "find_slots": "find_slots",
    "selection_parser": "selection_parser",
    "confirmation": "confirmation",
    "email_collection": "email_collection",
    "completed": END,
    END: END,
}

workflow.set_conditional_entry_point(route_conversation, router_map)

# After each node completes, it updates the stage and goes back to the router
# which then directs it to the next appropriate node.
for node_name in router_map.keys():
    if node_name not in [END, "completed"]: # END is not a real node
        workflow.add_conditional_edges(node_name, route_conversation, router_map)

app = workflow.compile()

# --- 6. Test the Integrated Graph ---
if __name__ == "__main__":
    import pandas as pd
    logger.info("🚀 Compiling the integrated agent graph...")
    
    try:
        patients_df = pd.read_csv(settings.PATIENTS_CSV_PATH)
        test_patient = patients_df[patients_df['visit_history'] > 0].iloc[0]
        patient_name = f"{test_patient['first_name']} {test_patient['last_name']}"
        patient_dob = test_patient['date_of_birth']
        logger.info(f"🧪 Using test patient: {patient_name} (DOB: {patient_dob})")
    except Exception as e:
        logger.error(f"❌ Could not load test patient: {e}")
        patient_name = "John Doe"
        patient_dob = "1990-01-01"
        logger.info(f"🧪 Using fallback test patient: {patient_name}")
    
    config = {"configurable": {"thread_id": "test-with-logging"}}

    logger.info(f"\n--- TEST CASE: Full Extended Conversation Flow ---")
    
    # Conversation turns to test the complete flow
    conversation_turns = [
        {
            "user_input": "Hi there!",
            "description": "Initial greeting"
        },
        {
            "user_input": f"My name is {patient_name} and my DOB is {patient_dob}.",
            "description": "Provide name and DOB"
        },
        {
            "user_input": "I'd like to see Dr. Smith at the Downtown Clinic.",
            "description": "Provide doctor and location"
        },
        {
            "user_input": "Yes, that's correct.",
            "description": "Confirm information"
        },
        {
            "user_input": "I'll take slot 1, please.",
            "description": "Select appointment slot"
        },
        {
            "user_input": "My email is test@example.com",
            "description": "Provide email"
        }
    ]
    
    for i, turn in enumerate(conversation_turns, 1):
        logger.info(f"\n--- TURN {i}: {turn['description']} ---")
        logger.info(f"👤 USER: {turn['user_input']}")
        
        try:
            # Invoke the conversation
            result = app.invoke({
                "messages": [{"role": "user", "content": turn['user_input']}]
            }, config)
            
            # Get the latest assistant message
            if result['messages']:
                last_assistant_message = None
                for msg in reversed(result['messages']):
                    if msg['role'] == 'assistant':
                        last_assistant_message = msg['content']
                        break
                
                if last_assistant_message:
                    logger.info(f"🤖 ASSISTANT: {last_assistant_message[:200]}...")
                    print(f"ASSISTANT: {last_assistant_message}")
            
            # Log state information
            logger.info(f"📊 Current stage: {result.get('conversation_stage', 'unknown')}")
            if result.get('patient_info'):
                pi = result['patient_info']
                logger.info(f"👤 Patient info: {pi.full_name}, {pi.date_of_birth}, {pi.preferred_doctor}, {pi.preferred_location}")
            if result.get('appointment_id'):
                logger.info(f"📅 Appointment ID: {result['appointment_id']}")
                
        except Exception as e:
            logger.error(f"❌ Error in turn {i}: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            break
    
    # Final verification
    logger.info("\n--- FINAL VERIFICATION ---")
    try:
        appointments_df = pd.read_csv(settings.APPOINTMENTS_CSV_PATH)
        if not appointments_df.empty:
            last_booking = appointments_df.iloc[-1]
            logger.info(f"✅ Appointment successfully written to appointments.csv")
            logger.info(f"   Appointment ID: {last_booking.get('appointment_id', 'N/A')}")
            logger.info(f"   Patient ID: {last_booking.get('patient_id', 'N/A')}")
            logger.info(f"   DateTime: {last_booking.get('datetime', 'N/A')}")
            print(f"✅ Final appointment booking verified!")
        else:
            logger.warning("⚠️ No appointments found in CSV")
            print("⚠️ No appointments found - data may not be persisting")
    except Exception as e:
        logger.error(f"⚠️ Error checking appointments: {e}")

    print("\n🎉 Extended conversation flow test completed!")