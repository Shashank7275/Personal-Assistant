# jarvis_search.py
import os
import requests
import asyncio
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool
from datetime import datetime  

# Setup logging for console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] %(message)s"
)

load_dotenv()

# ✅ Correct way to get keys (you can later replace with os.getenv)
GOOGLE_SEARCH_API_KEY = .............
SEARCH_ENGINE_ID = .........

@function_tool
async def search_internet(query: str) -> str:
    """
    Perform a Google Custom Search for the given query and return the top 3 results.
    """
    if not GOOGLE_SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        logging.error("Google Search API credentials not found in .env")
        return "Google Search API credentials not found in .env"

    url = (
        f"https://www.googleapis.com/customsearch/v1"
        f"?key={GOOGLE_SEARCH_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
    )

    try:
        # Run blocking requests.get() safely in async mode
        response = await asyncio.to_thread(requests.get, url, timeout=10)
        data = response.json()

        if "items" not in data:
            logging.warning(f"No results found for query: {query}")
            return f"No results found for: {query}"

        results = []
        for item in data["items"][:3]:
            title = item.get("title", "No title")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            results.append(f"{title}\n{snippet}\n{link}\n")

        # Print results in console
        logging.info(f"Search results for '{query}':\n" + "\n".join(results))

        return "\n\n".join(results)

    except Exception as e:
        logging.error(f"Error performing search: {e}")
        return f"Error performing search: {e}"



@function_tool
async def get_formatted_datetime() -> str:
    """
    Get the current date and time in a human-readable formatted string.
    Example: "Thursday, November 13, 2025 - 07:25 PM"
    """
    now = datetime.now()
    formatted = now.strftime("%A, %B %d, %Y - %I:%M %p")

    return formatted

