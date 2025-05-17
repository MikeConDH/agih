# Progress Report: AIMPEG AI Makerspace Public Event Generator

## Architecture
Three-agent system for AI event discovery and formatting:
- **ResearcherAgent**: Perplexity API integration for event discovery
- **ReporterAgent**: OpenAI GPT-4 for event formatting and Discord output
- **SupervisorAgent**: Quality control and workflow management

## Core Components
- `main.py`: Orchestrates agent workflow
- `agents/`: Core agent implementations
- `results/`: Output directory for events and state
- `.env`: API keys (OpenAI, Perplexity)
- `pyproject.toml`: Project dependencies and metadata

## Recent Milestones
1. Fixed Perplexity Client initialization
2. Implemented LLM-based event cleaning
3. Standardized Discord output format
4. Added day-of-week grouping
5. Implemented duplicate URL handling

## Current State
- Event discovery working
- Discord formatting implemented
- Day mapping corrected (May 19 = Monday)
- Basic error handling in place

## Backlog
1. **High Priority**
   - Improve event date validation
   - Add retry logic for API failures
   - Implement event deduplication

2. **Medium Priority**
   - Add event categorization improvements
   - Implement caching for API responses
   - Add unit tests

3. **Low Priority**
   - Add more event sources
   - Implement event filtering
   - Add monitoring and logging

## Getting Started
1. Set up `.env` with API keys
2. Install dependencies: `uv pip install -e .`
3. Run: `python main.py`

## Known Issues
- Some events may be missed due to date parsing
- Occasional formatting inconsistencies
- Limited error recovery 

## NEXT
1) DISCORD, Post
https://docs.google.com/document/d/1Dk7pHbl3eQugGyKGLTubUi0ua1q7hZB2mH1z6F8SARU/edit?usp=sharing
- MCP Server nict to have, just webhook for now, post and run.

2) MCP, Google, Other  
- Google MPC for my Calendar, Email, doc search
- Markdwon Formatter MCP (got to build one) 

3) FETCH, Wrapper 
4) FETCH AE
5) AIMPEG as an MCP (stretch)

##Appendix
https://docs.google.com/document/d/166RTnbr9voRb58YiblWkBTzI5QSO6_aryPLH_qWA1yw/edit?tab=t.0
