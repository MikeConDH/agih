import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import os
from datetime import datetime
from .utils import log_emoji
import logging

logger = logging.getLogger(__name__)

class ReporterAgent:
    def __init__(self):
        self.results_dir = "./results"
        os.makedirs(self.results_dir, exist_ok=True)
        self.output_file = "discord_events.txt"
        
        # Validate OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize OpenAI model for event formatting
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4-turbo-preview"  # Using GPT-4 for better formatting
        )
    
    def _save_to_file(self, formatted_events: str):
        """Save formatted events to file."""
        try:
            with open(self.output_file, "w") as f:
                f.write(formatted_events)
            logger.info(f"💾 Reporter: Output saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving output: {str(e)}")
    
    def format_events(self, events: List[Dict[str, Any]]) -> str:
        """Format events for Discord output."""
        log_emoji("✍️", "Reporter: Formatting events")
        try:
            # Get current week number
            current_week = datetime.now().isocalendar()[1]
            
            # Use LLM to format events
            prompt = f"""Format these AI events for Discord using this EXACT format:
            **[[Title]](URL)** (TYPE)[Category]

            Rules:
            1. Title should be clean, no markdown except the outer **
            2. URL must be included
            3. TYPE should be one of: INPERSON, ONLINE, or HYBRID
            4. Category should be one of: [Tech Session], [Workshop], [Conference], [Meetup], [Hackathon]
            5. Group events by day of the week
            6. Each day must start with a header in the format: **[DAY]** (e.g. **[MONDAY]**, **[TUESDAY]**, etc.)
            7. No descriptions, no dates, no times
            8. No additional text or comments
            9. Events must be grouped under their correct day of the week
            10. If multiple events have the same URL, only include one entry (the first one encountered)
            11. IMPORTANT: May 19, 2025 is a MONDAY. Map the days correctly:
                - May 19, 2025 = MONDAY
                - May 20, 2025 = TUESDAY
                - May 21, 2025 = WEDNESDAY
                - May 22, 2025 = THURSDAY
                - May 23, 2025 = FRIDAY
            12. Include ALL days from Monday to Friday, even if there are no events for a particular day

            Example format:
            **[MONDAY]**
            **[[AI Performance Engineering Meetup]](https://example.com/event)** (INPERSON)[Tech Session]

            **[TUESDAY]**
            **[[ML Workshop]](https://example.com/workshop)** (ONLINE)[Workshop]

            **[WEDNESDAY]**
            (no events)

            **[THURSDAY]**
            **[[AI Conference]](https://example.com/conference)** (INPERSON)[Conference]

            **[FRIDAY]**
            (no events)

            Events to format:
            {json.dumps(events, indent=2)}

            Return ONLY the formatted events, with day headers and proper grouping."""

            response = self.llm.invoke(prompt)
            formatted_content = response.content
            
            # Add week header
            markdown = f"**==================[ WEEK {current_week} EVENTS ]==================**\n\n"
            markdown += formatted_content
            
            log_emoji("✅", "Reporter: Events formatted successfully")
            return markdown
        except Exception as e:
            log_emoji("❌", f"Reporter: Error formatting events: {e}")
            return "Error formatting events"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the reporter agent."""
        logger.info("✍️ Reporter: Formatting events")
        
        try:
            events = state.get("events", [])
            if not events:
                logger.warning("No events to format")
                return state
            
            # Format events
            formatted_content = self.format_events(events)
            
            # Save to all output files
            self._save_to_file(formatted_content)  # discord_events.txt
            self.save_output(formatted_content)    # events.md and done file
            
            # Update state
            state["formatted_events"] = formatted_content
            state["status"] = "formatted"
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Reporter: Error formatting events: {str(e)}")
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    def save_output(self, content: str):
        log_emoji("💾", "Reporter: Saving output")
        try:
            # Save to results file
            with open(os.path.join(self.results_dir, "events.md"), "w") as f:
                f.write(content)
            
            # Create done file
            with open(os.path.join(self.results_dir, "done"), "w") as f:
                f.write("")
            
            log_emoji("✅", "Reporter: Output saved successfully")
        except Exception as e:
            log_emoji("❌", f"Reporter: Error saving output: {e}")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct calls to the reporter agent."""
        return self.run(state) 