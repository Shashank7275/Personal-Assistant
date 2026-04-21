import os
import subproces
import sys
import logging
from fuzzywuzzy import process

import asyncio
try:
    import pygetwindow as gw
except ImportError:
    gw = None

from langchain.tools import tool

sys.stdout.reconfigure(encoding='utf-8')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow")
        return False

    await asyncio.sleep(1.5)
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            logger.info(f"🪟 window focus में है: {window.title}")
            return True
    logger.warning("⚠ Focus करने के लिए window नहीं मिली।")
    return False

async def index_files(base_dirs):
    file_index = []
    for base_dir in base_dirs:
        for root, _, files in os.walk(base_dir):
            for f in files:
                file_index.append({
                    "name": f,
                    "path": os.path.join(root, f),
                    "type": "file"
                })
    logger.info(f"✅ {base_dirs} से कुल {len(file_index)} files को index किया गया।")
    return file_index

async def search_file(query, index):
    choices = [item["name"] for item in index]
    if not choices:
        logger.warning("⚠ Match करने के लिए कोई files नहीं हैं।")
        return None

    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' (Score: {score})")
    if score > 70:
        for item in index:
            if item["name"] == best_match:
                return item
    return None

async def open_file(item):
    try:
        logger.info(f"📂 File खोल रहे हैं: {item['path']}")
        if os.name == 'nt':
            os.startfile(item["path"])
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', item["path"]])
        await focus_window(item["name"])  # 👈 Focus window after opening
        return f"✅ File open हो गई।: {item['name']}"
    except Exception as e:
        logger.error(f"❌ File open करने में error आया।: {e}")
        return f"❌ File open करने में विफल रहा। {e}"

async def handle_command(command, index):
    item = await search_file(command, index)
    if item:
        return await open_file(item)
    else:
        logger.warning("❌ File नहीं मिली।")
        return "❌ File नहीं मिली।"

@tool
async def Play_file(name: str) -> str:

    """
    Searches for and opens a file by name from the D:/ drive.

    Use this tool when the user wants to open a file like a video, PDF, document, image, etc.
    Example prompts:
    - "D drive से my resume खोलो"
    - "Open D:/project report"
    - "MP4 file play करो"
    """


    folders_to_index = ["D:/"]
    index = await index_files(folders_to_index)
    command = name.strip()
    return await handle_command(command, index)



























