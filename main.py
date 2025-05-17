from typing import Dict, List, Any, Annotated, TypedDict
from langgraph.graph import StateGraph, END
from agents.researcher import ResearcherAgent
from agents.reporter import ReporterAgent
from agents.supervisor import SupervisorAgent
import json
import logging
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Print current directory and .env file existence
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f".env file exists: {os.path.exists('.env')}")

# Load environment variables
load_dotenv()

# Debug: Print environment variables (without values)
logger.info("Environment variables present:")
for key in ["OPENAI_API_KEY", "PERPLEXITY_API_KEY"]:
    logger.info(f"{key} is {'set' if os.getenv(key) else 'not set'}")

def validate_api_keys():
    """Validate that all required API keys are present."""
    required_keys = {
        "OPENAI_API_KEY": "OpenAI API key for GPT-4",
        "PERPLEXITY_API_KEY": "Perplexity API key for event search"
    }
    
    missing_keys = []
    for key, description in required_keys.items():
        if not os.getenv(key):
            missing_keys.append(f"{key} ({description})")
    
    if missing_keys:
        raise ValueError(
            "Missing required API keys. Please set the following environment variables:\n" +
            "\n".join(f"- {key}" for key in missing_keys)
        )

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
    # Validate API keys first
    validate_api_keys()
    
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