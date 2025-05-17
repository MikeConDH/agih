import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import json
from datetime import datetime, timedelta
import os
import re
from .utils import log_emoji, validate_event, parse_date
import logging
from perplexity import Client

logger = logging.getLogger(__name__)

class ResearcherAgent:
    def __init__(self):
        self.events = []
        
        # Validate API keys
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not os.getenv("PERPLEXITY_API_KEY"):
            raise ValueError("PERPLEXITY_API_KEY environment variable is not set")
        
        # Initialize Perplexity Client
        self.search_tool = Client()  # Perplexity client automatically uses the API key from environment
        
        # Initialize OpenAI model for event processing
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4-turbo-preview"  # Using GPT-4 for better event understanding
        )
        
        self.results_dir = "./results"
        os.makedirs(self.results_dir, exist_ok=True)
        self.sample_events = [
            {
                "title": "AI & Machine Learning Meetup",
                "date": "2025-05-20",
                "time": "18:00",
                "location": "San Francisco Tech Hub",
                "description": "Join us for an evening of AI discussions and networking",
                "url": "https://example.com/ai-meetup"
            }
        ]
    
    def save_midway(self, events: List[Dict]):
        """Save intermediate results"""
        with open(os.path.join(self.results_dir, "midway.json"), "w") as f:
            json.dump(events, f, indent=2)
    
    def _extract_event_details(self, text: str) -> Dict[str, Any]:
        """Extract structured event details from text."""
        # More comprehensive date patterns
        date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b',  # May 19, 2025
            r'\b\d{4}-\d{2}-\d{2}\b',  # 2025-05-19
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b'  # Monday, May 19, 2025
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        
        # Extract time if present
        time_pattern = r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b'
        times = re.findall(time_pattern, text)
        
        # Try to extract a title (first line or first sentence)
        title = text.split('\n')[0].strip() if text else ""
        if len(title) > 100:
            title = title[:97] + "..."
        
        return {
            "date": dates[0] if dates else None,
            "time": times[0] if times else None,
            "title": title,
            "raw_text": text
        }
    
    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate if an event matches our criteria."""
        if not event.get("title") or not event.get("date"):
            return False
            
        # Check if date is within our target range
        try:
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",  # 2025-05-19
                "%B %d, %Y",  # May 19, 2025
                "%A, %B %d, %Y"  # Monday, May 19, 2025
            ]
            
            event_date = None
            for date_format in date_formats:
                try:
                    event_date = datetime.strptime(event["date"], date_format)
                    break
                except ValueError:
                    continue
            
            if not event_date:
                return False
                
            # Target range: May 19-23, 2025
            target_start = datetime(2025, 5, 19)  # Monday
            target_end = datetime(2025, 5, 23)    # Friday
            return target_start <= event_date <= target_end
        except (ValueError, TypeError):
            return False
    
    def _search_events(self, query: str) -> List[Dict[str, Any]]:
        """Search for events using Perplexity Client."""
        try:
            print("\n🔍 ===== STARTING NEW SEARCH =====")
            print(f"Query: {query}")
            
            search_results = self.search_tool.search(query)
            
            # Extract the actual answer text from the Perplexity response
            if isinstance(search_results, dict) and 'text' in search_results:
                for item in search_results['text']:
                    if isinstance(item, dict) and item.get('step_type') == 'FINAL':
                        content = item.get('content', {})
                        if isinstance(content, dict) and 'answer' in content:
                            text = content['answer']
                            break
                else:
                    text = str(search_results)
            else:
                text = str(search_results)
            
            # Clean up the response
            text = text.replace('\\n', '\n').replace('\\"', '"')
            
            # Use LLM to clean and structure the events
            prompt = f"""Given the following text about AI events, extract and format the events into a clean list. 
            Remove any JSON artifacts, web results, or non-event content. Format each event with ONLY these fields:
            - Title (clean, no markdown)
            - Date (in YYYY-MM-DD format)
            - Location (if available)
            - URL (MUST be included, if not found in text, search for the event's website)
            - Type (Conference, Meetup, Workshop, or Hackathon)

            DO NOT include time or description fields.
            Each event MUST have a URL - if not found in the text, search for the event's official website.

            Text to process:
            {text}

            Return the events in a clean, structured format."""

            response = self.llm.invoke(prompt)
            cleaned_text = response.content
            
            # Split into potential events
            event_blocks = []
            current_block = []
            
            for line in cleaned_text.split('\n'):
                line = line.strip()
                if not line:
                    if current_block:
                        event_blocks.append('\n'.join(current_block))
                        current_block = []
                elif line.startswith(('###', '- **', '* **', '**')):
                    if current_block:
                        event_blocks.append('\n'.join(current_block))
                        current_block = []
                    current_block.append(line)
                else:
                    current_block.append(line)
            
            if current_block:
                event_blocks.append('\n'.join(current_block))
            
            events = []
            for block in event_blocks:
                if not block.strip():
                    continue
                
                # Skip summary blocks and JSON artifacts
                if any(skip in block.lower() for skip in ['summary', 'in summary', 'overview', 'note:', 'while there are']):
                    continue
                if block.startswith('{') or block.startswith('"answer":'):
                    continue
                
                # Extract event details
                event_details = self._extract_event_details(block)
                
                if event_details["date"]:
                    # Clean up the title
                    title = event_details["title"]
                    
                    # Remove markdown and formatting
                    title = re.sub(r'^\*\*|\*\*$', '', title)  # Remove markdown bold
                    title = re.sub(r'^\[.*?\]', '', title)  # Remove [link] prefix
                    title = re.sub(r'\(pplx://.*?\)', '', title)  # Remove Perplexity links
                    title = re.sub(r'^###\s*', '', title)  # Remove markdown headers
                    title = re.sub(r'^\s*[-•*]\s*', '', title)  # Remove bullet points
                    title = re.sub(r'^"|"$', '', title)  # Remove quotes
                    title = re.sub(r',\s*$', '', title)  # Remove trailing commas
                    title = title.strip()
                    
                    # Determine event type
                    event_type = "Conference"
                    if any(word in block.lower() for word in ['meetup', 'networking']):
                        event_type = "Meetup"
                    elif any(word in block.lower() for word in ['workshop', 'training']):
                        event_type = "Workshop"
                    elif any(word in block.lower() for word in ['hackathon']):
                        event_type = "Hackathon"
                    
                    # Extract URL from the block
                    url = None
                    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
                    urls = re.findall(url_pattern, block)
                    if urls:
                        url = urls[0]
                    
                    event = {
                        "title": title,
                        "date": event_details["date"],
                        "location": "San Francisco",
                        "url": url,
                        "type": event_type
                    }
                    
                    if self._validate_event(event):
                        events.append(event)
            
            return events
        except Exception as e:
            print(f"\n💥 ERROR: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def scrape_events(self) -> List[Dict]:
        log_emoji("🔍", "Starting event search...")
        
        # List of search queries to try
        search_queries = [
            "List all AI events happening in San Francisco from May 19 to May 23, 2025, including meetups, workshops, hackathons, and conferences. Include links and event details, check the Generative AI SF Events Calendar and Cerebral Valley Site and the following list here: https://docs.google.com/spreadsheets/d/1P6ut7vL-gXKbeDeh3nuPqBjoCupjIt87Sw7TnhumBSU/edit?gid=1781893986#gid=1781893986",
            "AI events San Francisco May 19-23 2025",
            "Artificial Intelligence meetups San Francisco next week",
            "AI conferences San Francisco May 2025",
            "Machine Learning events San Francisco May 19-23",
            "AI events Cerebral Valley San Francisco May 19-23 2025",
            "Cerebral Valley AI meetups San Francisco May 2025"
        ]
        
        all_events = []
        for query in search_queries:
            events = self._search_events(query)
            all_events.extend(events)
        
        # If no events found, use sample data
        if not all_events:
            logger.info("ℹ️ No events found, using sample data")
            all_events = self.sample_events
        
        # Save intermediate results
        self.save_midway(all_events)
        log_emoji("💾", "Saved intermediate results to midway.json")
        
        log_emoji("✅", f"Found {len(all_events)} events")
        return all_events
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the researcher agent."""
        logger.info("🎯 Researcher agent activated")
        
        # Search for events
        events = self.scrape_events()
        
        # Update state
        state["events"] = events
        state["status"] = "events_found"
        
        return state 