# app.py
# This is the main file for the Streamlit user interface.

import streamlit as st
import sys
import os
import uuid

# --- FIX FOR STREAMLIT RUN ---
# Add the project root to the Python path to allow imports from other folders.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
# --- END FIX ---

# --- Import the LangGraph Application ---
from main_graph import app as medical_agent_app

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="AI Medical Scheduler",
    page_icon="🏥",
    layout="centered"
)

st.title("🏥 AI Medical Appointment Scheduler")
st.markdown("""
Welcome! I can help you book a medical appointment. 
To get started, please tell me your **full name** and **date of birth**.
""")

# --- 2. Session State Management ---
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = str(uuid.uuid4())
if 'agent_state' not in st.session_state:
    st.session_state.agent_state = {}
if 'processing' not in st.session_state:
    st.session_state.processing = False

# --- 3. Chat Interface Logic ---

# Display all existing messages (single source of truth)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Get user input
prompt = st.chat_input("Your response here...")
if prompt and not st.session_state.processing:
    # Set processing flag to prevent multiple submissions
    st.session_state.processing = True
    
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display the user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process with agent
    with st.spinner("Thinking..."):
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        try:
            # Prepare current state for agent
            current_state = st.session_state.agent_state.copy()
            current_state['messages'] = st.session_state.messages.copy()
            
            # Invoke the agent
            result = medical_agent_app.invoke(current_state, config=config)
            
            # Update agent state
            st.session_state.agent_state = result
            
            # Find new messages from agent (everything after our current messages)
            if 'messages' in result:
                current_msg_count = len(st.session_state.messages)
                agent_messages = result['messages']
                
                # Add only new messages that aren't already in our state
                for i in range(current_msg_count, len(agent_messages)):
                    new_msg = agent_messages[i]
                    if new_msg not in st.session_state.messages:
                        st.session_state.messages.append(new_msg)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant", 
                 "content": f"Sorry, I encountered an error: {str(e)}"
            })
    
    # Reset processing flag and rerun to show all messages
    st.session_state.processing = False
    st.rerun()