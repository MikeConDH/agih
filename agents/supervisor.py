from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from .utils import log_emoji
import logging
import os
import json

logger = logging.getLogger(__name__)

class SupervisorAgent:
    def __init__(self):
        self.state = {"events": [], "status": "initialized"}
        
        # Validate OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize OpenAI model for supervision
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4-turbo-preview"  # Using GPT-4 for better supervision
        )
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if not last_message:
            log_emoji("🎯", "Supervisor: Starting workflow")
            return {
                "messages": [HumanMessage(content="Find AI events in SF for the upcoming week")],
                "events": [],
                "status": "searching",
                "next": "researcher"
            }
        
        if last_message.type == "ai" and "researcher" in state.get("current_node", ""):
            log_emoji("📥", "Supervisor: Received events from researcher")
            return {
                "messages": [HumanMessage(content="Format these events for Discord")],
                "events": state.get("events", []),
                "status": "formatting",
                "next": "reporter"
            }
        
        if last_message.type == "ai" and "reporter" in state.get("current_node", ""):
            log_emoji("✅", "Supervisor: Task completed")
            return {
                "messages": [AIMessage(content="Task completed successfully")],
                "events": state.get("events", []),
                "status": "completed",
                "next": "end"
            }
        
        log_emoji("⚠️", "Supervisor: Unexpected state")
        return {
            "messages": [AIMessage(content="Unexpected state")],
            "events": state.get("events", []),
            "status": "error",
            "next": "end"
        }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the supervisor agent."""
        logger.info("🧑‍💼 Supervisor: Reviewing events")
        
        # Get events from state
        events = state.get("events", [])
        
        # Use LLM to review events and determine next steps
        prompt = f"""Review these AI events and determine if they are properly formatted and complete.
        Events to review:
        {json.dumps(events, indent=2)}
        
        Consider:
        1. Are all required fields present (title, date, location, description)?
        2. Are the dates within the target range (May 19-23, 2025)?
        3. Are the events properly categorized (Conference, Meetup, Workshop, Hackathon)?
        4. Are there any duplicates or invalid entries?
        
        Return a JSON object in this exact format:
        {{
            "status": "ready" or "needs_review",
            "message": "A brief summary of the review",
            "next_step": "reporter" or "researcher"
        }}

        Make sure to return ONLY the JSON object, with no additional text or explanation."""

        response = self.llm.invoke(prompt)
        try:
            review = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            review = {
                "status": "needs_review",
                "message": "Error parsing LLM response, defaulting to review",
                "next_step": "researcher"
            }
        
        # Update state based on LLM review
        state["status"] = review["status"]
        state["next"] = review["next_step"]
        state["review_message"] = review["message"]
        
        # Log the review
        logger.info(f"📊 Supervisor: {review['message']}")
        logger.info(f"📊 Supervisor: Reviewed {len(events)} events")
        
        return state 