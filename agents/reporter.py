import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
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
    
    def _format_event(self, event: Dict[str, Any]) -> str:
        """Format a single event for Discord."""
        try:
            # Format date and time
            date_str = event.get("date", "TBD")
            time_str = event.get("time", "TBD")
            
            # Format location
            location = event.get("location", "San Francisco")
            
            # Format description (truncate if too long)
            description = event.get("description", "")
            if len(description) > 200:
                description = description[:197] + "..."
            
            # Format URL if available
            url = event.get("url", "")
            url_str = f"\n🔗 {url}" if url else ""
            
            # Create Discord-formatted message
            return f"""**{event.get('title', 'Untitled Event')}**
📅 {date_str} at {time_str}
📍 {location}
📝 {description}{url_str}
-------------------"""
        except Exception as e:
            logger.error(f"Error formatting event: {str(e)}")
            return f"Error formatting event: {str(e)}"
    
    def _save_to_file(self, formatted_events: str):
        """Save formatted events to file."""
        try:
            with open(self.output_file, "w") as f:
                f.write(formatted_events)
            logger.info(f"💾 Reporter: Output saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving output: {str(e)}")
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the reporter agent."""
        logger.info("✍️ Reporter: Formatting events")
        
        try:
            events = state.get("events", [])
            if not events:
                logger.warning("No events to format")
                return state
            
            # Format each event
            formatted_events = []
            for event in events:
                formatted_event = self._format_event(event)
                formatted_events.append(formatted_event)
            
            # Join all formatted events
            final_output = "\n\n".join(formatted_events)
            
            # Save to file
            self._save_to_file(final_output)
            
            # Update state
            state["formatted_events"] = final_output
            state["status"] = "formatted"
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Reporter: Error formatting events: {str(e)}")
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    def format_events(self, events_str: str) -> str:
        log_emoji("✍️", "Reporter: Formatting events")
        try:
            events = json.loads(events_str)
            
            # Get current week number
            current_week = datetime.now().isocalendar()[1]
            
            # Start building the markdown
            markdown = f"**==================[ WEEK {current_week} EVENTS ]==================**\n\n"
            
            # Group events by day
            events_by_day = {}
            for event in events:
                day = event["Date"].split(",")[0]  # Get the day name
                if day not in events_by_day:
                    events_by_day[day] = []
                events_by_day[day].append(event)
            
            # Format each day's events
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
                if day in events_by_day:
                    markdown += f"**[ {day} ]**\n"
                    for event in events_by_day[day]:
                        markdown += f"**[[{event['Title']}]]({event['URL']})** ({event['Location']})[{event['Type']}]\n"
                    markdown += "\n"
            
            log_emoji("✅", "Reporter: Events formatted successfully")
            return markdown
        except Exception as e:
            log_emoji("❌", f"Reporter: Error formatting events: {e}")
            return "Error formatting events"
    
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
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message and last_message.type == "human":
            log_emoji("🎯", "Reporter: Processing events")
            
            # Format events
            formatted_content = self.format_events(last_message.content)
            
            # Save output
            self.save_output(formatted_content)
            
            return {
                "messages": [AIMessage(content="Events formatted and saved successfully")],
                "events": state.get("events", []),
                "status": "completed",
                "next": "end"
            }
        
        log_emoji("⚠️", "Reporter: No events to format")
        return {
            "messages": [AIMessage(content="No events to format")],
            "events": state.get("events", []),
            "status": "error",
            "next": "end"
        } 