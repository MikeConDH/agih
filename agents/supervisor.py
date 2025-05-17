from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from .utils import log_emoji
import logging

logger = logging.getLogger(__name__)

class SupervisorAgent:
    def __init__(self):
        self.state = {"events": [], "status": "initialized"}
    
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
            self.state["events"] = last_message.content
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
        
        # Update state
        state["status"] = "supervised"
        
        # Log the number of events
        logger.info(f"📊 Supervisor: Reviewed {len(events)} events")
        
        return state 