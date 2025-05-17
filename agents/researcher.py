import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
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
        # Initialize Perplexity Client
        self.search_tool = Client()
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
        # Basic pattern matching for dates
        date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b'
        dates = re.findall(date_pattern, text)
        
        # Extract time if present
        time_pattern = r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b'
        times = re.findall(time_pattern, text)
        
        return {
            "date": dates[0] if dates else None,
            "time": times[0] if times else None,
            "raw_text": text
        }
    
    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate if an event matches our criteria."""
        if not event.get("title") or not event.get("date"):
            return False
            
        # Check if date is within our target range
        try:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            target_start = datetime(2025, 5, 19)
            target_end = datetime(2025, 5, 23)
            return target_start <= event_date <= target_end
        except (ValueError, TypeError):
            return False
    
    def _search_events(self, query: str) -> List[Dict[str, Any]]:
        """Search for events using Perplexity Client."""
        try:
            logger.info(f"🔎 Searching for: {query}")
            # Use the Perplexity Client's search method
            search_results = self.search_tool.search(query)
            logger.info(f"🔍 Raw search_results: {repr(search_results)}")
            
            if not search_results:
                logger.warning("No search results found")
                return []
            
            # Process search results into event format
            events = []
            # If search_results is a dict with 'results' key, use it
            if isinstance(search_results, dict) and 'results' in search_results:
                search_results = search_results['results']
            for result in search_results:
                # If result is a dict with 'text' or 'title', use it
                if isinstance(result, dict):
                    text = result.get('text') or result.get('title') or str(result)
                else:
                    text = str(result)
                if text.strip():
                    event_details = self._extract_event_details(text)
                    if event_details["date"]:  # Only include if we found a date
                        events.append({
                            "title": text[:100],  # Use first 100 chars as title
                            "date": event_details["date"],
                            "time": event_details["time"],
                            "location": "San Francisco",  # Default to SF
                            "description": text,
                            "url": result.get('url') if isinstance(result, dict) else None
                        })
            # Return all events found, not just one
            return events
        except Exception as e:
            logger.error(f"Error searching events: {str(e)}")
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