from typing import Dict, List, Any, Annotated, TypedDict
from langgraph.graph import StateGraph, END
from agents.researcher import ResearcherAgent
from agents.reporter import ReporterAgent
from agents.supervisor import SupervisorAgent
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define state types
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    status: str

def create_workflow() -> StateGraph:
    # Initialize agents
    researcher = ResearcherAgent()
    reporter = ReporterAgent()
    supervisor = SupervisorAgent()
    
    # Create workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("researcher", researcher.run)
    workflow.add_node("reporter", reporter.run)
    workflow.add_node("supervisor", supervisor.run)
    
    # Define edges
    workflow.add_edge("researcher", "reporter")
    workflow.add_edge("reporter", "supervisor")
    workflow.add_edge("supervisor", END)
    
    # Set entry point
    workflow.set_entry_point("researcher")
    
    return workflow

def run():
    # Create workflow
    app = create_workflow()
    
    # Compile workflow
    app = app.compile()
    
    # Initialize state
    initial_state = {
        "messages": [],
        "events": [],
        "status": "started"
    }
    
    # Run workflow
    logger.info("🎯 Supervisor: Starting workflow")
    result = app.invoke(initial_state)
    
    # Save final results
    with open("final_results.json", "w") as f:
        json.dump(result, f, indent=2)
    logger.info("💾 Final results saved to final_results.json")

if __name__ == "__main__":
    run() 