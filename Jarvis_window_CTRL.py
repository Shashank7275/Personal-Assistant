import os
import subprocess
import logging
import sys
import asyncio
import webbrowser
from fuzzywuzzy import process

try:
    from livekit.agents import function_tool
except ImportError:
    def function_tool(func):
        return func

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import pyautogui
except Exception:
    pyautogui = None

from keyboard_mouse_CTRL import type_text_tool

# ===================== LOGGER ===================== #
sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS-WINDOW")

# ===================== APP MAP ===================== #
APP_MAPPINGS = {
    # English
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "chrome": "chrome",
    "google chrome": "chrome",
    "vlc": "vlc",
    "cmd": "cmd",
    "command prompt": "cmd",
    "paint": "mspaint",
    'camera": "camera",

        # URLs
    "youtube": "https://www.youtube.com",
    "whatsapp": "whatsapp://",

    # Hindi
    "युटुब": "https://www.youtube.com",
    "यूट्यूब": "https://www.youtube.com",
    "व्हाट्सएप": "whatsapp://",
    "क्रोम": "chrome",
    "गूगल क्रोम": "chrome",
    "कैलकुलेटर": "calc",
    "नोटपैड": "notepad",
    "पेंट": "mspaint",
}

FOCUS_TITLES = {
    "notepad": "Notepad",
    "calc": "Calculator",
    "chrome": "Google Chrome",
    "vlc": "VLC",
    "cmd": "Command Prompt",
    "youtube": "YouTube",
    "whatsapp": "WhatsApp",
}

# ===================== UTIL ===================== #
def normalize_command(text: str) -> str:
    """
    Removes Hindi/English open keywords safely and extracts the app name
    """
    REMOVE_WORDS = [
        "open", "opening", "opened",
        "खोलो", "खोल", "ओपन", "ओपनिंग", "करो",
        "और", "उसमें", "लिख", "दो", "हेलो", "जार्विस", "व्हाट", "आर", "यू", "डूइंग"
    ]
    text = text.lower()
    for w in REMOVE_WORDS:
        text = text.replace(w, "")
    # Take the first meaningful word
    words = text.strip().split()
    if words:
        return words[0]
    return text.strip()

async def focus_window(title: str):
    if not gw:
        return False
    await asyncio.sleep(1.2)
    for w in gw.getAllWindows():
        if title.lower() in w.title.lower():
            if w.isMinimized:
                w.restore()
            w.activate()
            return True
    return False

def fuzzy_match_app(app_name: str) -> str:
    keys = list(APP_MAPPINGS.keys())
    match, score = process.extractOne(app_name, keys)
    if score >= 70:
        return match
    return app_name

# ===================== OPEN APP ===================== #
@function_tool
async def open(full_command: str) -> str:
    try:
        clean = normalize_command(full_command)
        matched_key = fuzzy_match_app(clean)
        app = APP_MAPPINGS.get(matched_key, matched_key)

        logger.info(f"OPEN → raw='{full_command}' clean='{clean}' match='{matched_key}'")

        # 🌐 URL → browser or desktop app
        if app.startswith("http"):
            webbrowser.open(app)
            await asyncio.sleep(3)  # Wait for browser to open
            if "youtube" in matched_key.lower():
                await focus_window("YouTube")
            elif "whatsapp" in matched_key.lower():
                # For web WhatsApp, ensure focus
                await focus_window("WhatsApp")
        elif app.startswith("whatsapp://"):
            try:
                # Try to open desktop app via URI scheme
                subprocess.Popen([app], shell=True) # Use shell=True for URI schemes on Windows
                await asyncio.sleep(5)  # Give time for app to open
                await focus_window("WhatsApp")
            except Exception as uri_e:
                logger.warning(f"Failed to open WhatsApp desktop app via URI: {uri_e}. Falling back to web.")
                webbrowser.open("https://web.whatsapp.com")
                await asyncio.sleep(5)
                await focus_window("WhatsApp")
        else:
            # 🪟 Try Start Menu (non-blocking)
            if pyautogui:
                try:
                    await asyncio.to_thread(pyautogui.press, "win")
                    await asyncio.sleep(0.5)
                    await asyncio.to_thread(pyautogui.write, matched_key, 0.05)
                    await asyncio.sleep(0.4)
                    await asyncio.to_thread(pyautogui.press, "enter")
                except Exception:
                    pass

            # 🧨 FINAL fallback (NO TIMEOUT)
            subprocess.Popen(app, shell=True)

            # 🎯 Focus
            title = FOCUS_TITLES.get(matched_key)
            if title:
                await focus_window(title)

        # ✍️ Check for writing
        write_text = None
        if "write" in full_command.lower():
            parts = full_command.lower().split("write", 1)
            if len(parts) > 1:
                write_text = parts[1].strip()
        elif "लिख" in full_command:
            parts = full_command.split("लिख", 1)
            if len(parts) > 1:
                write_text = parts[1].strip()
                # Remove "दो" if present
                if write_text.startswith("दो "):
                    write_text = write_text[3:].strip()

        if write_text:
            await asyncio.sleep(2)  # Wait for app to open
            result = await type_text_tool(write_text)
            return f"🚀 {matched_key} खोल दिया गया है और {result}"

        return f"🚀 {matched_key} खोल दिया गया है"

    except Exception as e:
        logger.error(e)
        return f"❌ App open नहीं हो पाया: {e}"

# ===================== CLOSE WINDOW ===================== #
@function_tool
async def close(window_name: str) -> str:
    if not win32gui:
        return "❌ win32gui available नहीं है"

    window_name = window_name.lower()

    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            if window_name in title:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

    win32gui.EnumWindows(enum_handler, None)
    return f"🗑️ {window_name} बंद कर दिया गया है"

@function_tool
async def folder_file(path: str) -> str:
    return "❌ folder_file tool not implemented"


