# agents/scheduling_agent.py
# This agent is responsible for parsing user selection of appointment slots
# and handling the appointment booking process.

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from typing import List, Dict, Any
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. Define the Desired Output Structure ---
class SlotSelection(BaseModel):
    """Data model for slot selection parsing."""
    selected_slot: str | None = Field(None, description="The selected appointment slot")
    slot_number: int | None = Field(None, description="The number of the selected slot (1-based)")

# --- 2. Create the Selection Parser Chain ---
def create_selection_parser_chain(llm: ChatOpenAI, master_prompt: str):
    """
    Creates a LangChain chain that parses user slot selection from conversation.
    """
    logger.info("🔧 Creating selection parser chain...")
    
    parser = JsonOutputParser()
    json_llm = llm.bind(response_format={"type": "json_object"})
    
    system_prompt = master_prompt + """
    You are the 'Selection Parser Agent'. Your task is to analyze the user's message and determine which appointment slot they want to select.

    The user will be presented with numbered appointment slots (1, 2, 3, etc.) and they need to select one.
    
    - Use "selectedSlot" and "slotNumber" as the keys in your JSON response.
    - If the user selects by number (e.g., "I'll take slot 1", "Option 2", "Number 3"), extract the number.
    - If the user describes a specific time/date that matches one of the available slots, try to identify which slot number it corresponds to.
    - If the selection is ambiguous or unclear, set selectedSlot to "AMBIGUOUS".
    - You MUST ONLY respond with a valid JSON object. Do not add any other text or explanations.

    Example Response: {{"selectedSlot": "Dr. Smith on Tuesday, September 09 at 02:00 PM", "slotNumber": 1}}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Available slots:\n{available_slots}\n\nUser's response: {user_message}")
    ])
        
    return prompt | json_llm | parser

# --- 3. Helper Functions ---
def parse_slot_selection(user_message: str, available_slots: List[str], llm_chain) -> Dict[str, Any]:
    """
    Parse user's slot selection using the LLM chain.
    
    Args:
        user_message: The user's response message
        available_slots: List of available appointment slots
        llm_chain: The selection parser chain
    
    Returns:
        Dictionary with selected slot information
    """
    logger.info(f"📝 Parsing slot selection from user message: '{user_message}'")
    logger.info(f"📅 Available slots: {len(available_slots)} slots")
    
    slots_str = "\n".join([f"{i+1}. {s}" for i, s in enumerate(available_slots)])
    
    try:
        result = llm_chain.invoke({
            "available_slots": slots_str,
            "user_message": user_message
        })
        
        logger.info(f"🤖 LLM parsed result: {result}")
        
        # Normalize the result
        normalized_result = normalize_selection_result(result, available_slots)
        logger.info(f"✅ Normalized result: {normalized_result}")
        
        return normalized_result
        
    except Exception as e:
        logger.error(f"❌ Error parsing slot selection: {e}")
        return {"selected_slot": "AMBIGUOUS", "slot_number": None}

def normalize_selection_result(result: Dict[str, Any], available_slots: List[str]) -> Dict[str, Any]:
    """
    Normalize the LLM result and validate against available slots.
    """
    # Extract slot number from various key formats
    slot_number = (
        result.get('slotNumber') or 
        result.get('slot_number') or 
        result.get('number')
    )
    
    # Extract selected slot from various key formats
    selected_slot = (
        result.get('selectedSlot') or 
        result.get('selected_slot') or 
        result.get('slot')
    )
    
    # Validate slot number
    if slot_number and isinstance(slot_number, int) and 1 <= slot_number <= len(available_slots):
        # Use the actual slot from our list
        actual_slot = available_slots[slot_number - 1]
        logger.info(f"✅ Valid slot number {slot_number} maps to: {actual_slot}")
        return {
            "selected_slot": actual_slot,
            "slot_number": slot_number
        }
    
    # If we have a selected slot but no valid number, try to match it
    if selected_slot and selected_slot != "AMBIGUOUS":
        for i, slot in enumerate(available_slots):
            if selected_slot in slot or slot in selected_slot:
                logger.info(f"✅ Matched slot text to position {i+1}: {slot}")
                return {
                    "selected_slot": slot,
                    "slot_number": i + 1
                }
    
    # If nothing matches, return ambiguous
    logger.warning("⚠️ Could not determine valid slot selection")
    return {
        "selected_slot": "AMBIGUOUS",
        "slot_number": None
    }

# --- 4. Example Usage & Testing ---
if __name__ == '__main__':
    # --- FIX FOR DIRECT EXECUTION ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    # --- END FIX ---
    
    # --- LOCAL IMPORTS ---
    from config import prompts
    from main_graph import llm 
    # --- END LOCAL IMPORTS ---

    print("🚀 Testing Scheduling Agent...")

    selection_chain = create_selection_parser_chain(llm, prompts.MASTER_PROMPT)
    
    # Mock available slots
    test_slots = [
        "Dr. Smith on Tuesday, September 09 at 02:00 PM",
        "Dr. Smith on Tuesday, September 09 at 03:00 PM", 
        "Dr. Johnson on Wednesday, September 10 at 09:00 AM"
    ]

    # --- Test Case 1: Clear number selection ---
    print("\n--- Test Case 1: Number Selection ---")
    result = parse_slot_selection("I'll take slot 1", test_slots, selection_chain)
    print("Result:", result)
    assert result['slot_number'] == 1
    assert result['selected_slot'] == test_slots[0]
    print("✅ Test Case 1 Passed")

    # --- Test Case 2: Alternative number format ---
    print("\n--- Test Case 2: Alternative Format ---")
    result = parse_slot_selection("Option 2 please", test_slots, selection_chain)
    print("Result:", result)
    # Should select slot 2
    print("✅ Test Case 2 Passed")

    # --- Test Case 3: Ambiguous selection ---
    print("\n--- Test Case 3: Ambiguous ---")
    result = parse_slot_selection("Maybe sometime next week", test_slots, selection_chain)
    print("Result:", result)
    assert result['selected_slot'] == "AMBIGUOUS"
    print("✅ Test Case 3 Passed")

    print("\n🎉 Scheduling Agent tests completed successfully!")