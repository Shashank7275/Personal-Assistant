import asyncio
import re
import shutil
import pytesseract
import pyttsx3
import mss
import cv2
import numpy as np
import os
import sys
import logging

# ✅ SILENCE COM TYPES & PYTTSX3 LOGS
logging.getLogger('comtypes').setLevel(logging.WARNING)
logging.getLogger('pyttsx3').setLevel(logging.WARNING)

from PIL import Image
from pathlib import Path
import subprocess
import platform

try:
    import fitz  # PyMuPDF for PDF reading
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

from livekit.agents import function_tool

# ================= OCR SETUP =================
TESSERACT_PATH = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
TESSERACT_NOT_FOUND_MSG = ""

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    if platform.system() == "Windows":
        TESSERACT_NOT_FOUND_MSG = (
            "Tesseract OCR is not installed or not found in PATH. "
            "Please install it from https://tesseract-ocr.github.io/tessdoc/Downloads.html, "
            "ensure it's added to your system's PATH, or set the TESSERACT_CMD environment variable "
            "(e.g., TESSERACT_CMD='C:\\Program Files\\Tesseract-OCR\\tesseract.exe')."
        )
    else:
        TESSERACT_NOT_FOUND_MSG = "Tesseract OCR is not installed or not found in PATH. Please install it according to your OS or set the TESSERACT_CMD environment variable."

# ================= VOICE =====================
engine = pyttsx3.init()
engine.setProperty("rate", 165)

def jarvis_speak(text):
    """Speak text using TTS"""
    print("JARVIS:", text)
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")

def jarvis_read_text(text, max_length=800):
    """Read text with smart truncation"""
    if not text or not text.strip():
        jarvis_speak("No text found to read.")
        return
    
    # Clean and truncate text
    clean_text = text.strip()
    if len(clean_text) > max_length:
        truncated = clean_text[:max_length] + "... (truncated)"
        jarvis_speak(truncated)
    else:
        jarvis_speak(clean_text)

# ================= FILE READING =================
def read_text_file(file_path):
    """Read plain text files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-16') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1252') as file:
                    return file.read()
            except Exception as e:
                return f"Error reading text file with multiple encodings: {e}"
    except Exception as e:
        return f"Error reading text file: {e}"

def read_pdf_file(file_path):
    """Read PDF files using PyMuPDF"""
    if not PDF_SUPPORT:
        return "PDF support not available. Please install PyMuPDF: pip install PyMuPDF"
    
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def read_word_file(file_path):
    """Read Word documents"""
    if not DOCX_SUPPORT:
        return "Word document support not available. Please install python-docx: pip install python-docx"
    
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error reading Word document: {e}"

def read_any_file(file_path):
    """Universal file reader that handles multiple formats"""
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log']:
        return read_text_file(file_path)
    elif file_extension == '.pdf':
        return read_pdf_file(file_path)
    elif file_extension == '.docx':
        return read_word_file(file_path)
    elif file_extension == '.doc':
        return "Unsupported file format: .doc. Please convert to .docx or .pdf. The python-docx library does not support the legacy .doc format."
    else:
        # Try to read as text file as fallback
        result = read_text_file(file_path)
        if "Error reading text file" in result:
            return f"Unsupported file format: {file_extension}. Supported formats: .txt, .pdf, .docx, .py, .js, .html, .css, .json, .xml, .csv, .log"
        return result

# ================= OCR LOGIC =================
def read_screen_once():
    """Read text from screen using OCR"""
    if not TESSERACT_PATH:
        return TESSERACT_NOT_FOUND_MSG

    try:
        with mss.mss() as sct:
            # Get the primary monitor
            monitor = sct.monitors[1]
            img = np.array(sct.grab(monitor))
            
            # Convert to grayscale and enhance for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Apply threshold to get better contrast
            gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            # Apply some denoising
            gray = cv2.medianBlur(gray, 3)
            
            # Perform OCR
            text = pytesseract.image_to_string(Image.fromarray(gray))
            
            if not text.strip():
                return "No text detected on screen. Make sure text is visible and not too small."
            
            return text.strip()
    except Exception as e:
        return f"Error reading screen: {e}"

def read_specific_area(x, y, width, height):
    """Read text from a specific screen area"""
    if not TESSERACT_PATH:
        return TESSERACT_NOT_FOUND_MSG

    try:
        with mss.mss() as sct:
            # Define the specific area
            monitor = {"top": y, "left": x, "width": width, "height": height}
            img = np.array(sct.grab(monitor))
            
            # Process image for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            gray = cv2.medianBlur(gray, 3)
            
            text = pytesseract.image_to_string(Image.fromarray(gray))
            return text.strip() if text.strip() else "No text detected in the specified area."
    except Exception as e:
        return f"Error reading screen area: {e}"

# ================= FUNCTION TOOLS =================
@function_tool
async def read_file_tool(file_path: str) -> str:
    """Read any text-based file (txt, pdf, docx, code files, etc.)"""
    try:
        content = read_any_file(file_path)
        if "Error" in content or "not found" in content or "not available" in content:
            return f"❌ {content}"
        
        # Truncate for voice output
        if len(content) > 1000:
            return f"📄 File content (first 1000 chars):\n{content[:1000]}...\n💡 Full content has {len(content)} characters"
        else:
            return f"📄 File content:\n{content}"
    except Exception as e:
        return f"❌ Error reading file: {e}"

@function_tool
async def read_screen_tool() -> str:
    """Read text from the entire screen using OCR"""
    try:
        text = read_screen_once()
        if "Error" in text or "not installed" in text:
            return f"❌ {text}"
        
        if len(text) > 800:
            return f"📺 Screen text (first 800 chars):\n{text[:800]}...\n💡 Full text has {len(text)} characters"
        else:
            return f"📺 Screen text:\n{text}"
    except Exception as e:
        return f"❌ Error reading screen: {e}"

@function_tool
async def read_screen_area_tool(x: int, y: int, width: int, height: int) -> str:
    """Read text from a specific screen area using OCR"""
    try:
        text = read_specific_area(x, y, width, height)
        if "Error" in text or "not installed" in text:
            return f"❌ {text}"
        
        if len(text) > 500:
            return f"📺 Area text (first 500 chars):\n{text[:500]}...\n💡 Full text has {len(text)} characters"
        else:
            return f"📺 Area text:\n{text}"
    except Exception as e:
        return f"❌ Error reading screen area: {e}"

@function_tool
async def list_supported_formats_tool() -> str:
    """List all supported file formats for reading"""
    formats = {
        "Text Files": [".txt", ".py", ".js", ".html", ".css", ".json", ".xml", ".csv", ".log"],
        "PDF Files": [".pdf"],
        "Word Documents": [".docx", ".doc"],
        "Screen Reading": "OCR for any text on screen"
    }
    
    result = "📚 Supported file formats:\n"
    for category, extensions in formats.items():
        result += f"\n{category}: {', '.join(extensions) if isinstance(extensions, list) else extensions}"
    
    if not PDF_SUPPORT:
        result += "\n\n⚠️ PDF support: Not available (install PyMuPDF)"
    if not DOCX_SUPPORT:
        result += "\n⚠️ Word support: Not available (install python-docx)"
    if not TESSERACT_PATH:
        result += "\n⚠️ OCR support: Not available (install Tesseract OCR)"
    
    return result

# ================= MAIN FUNCTIONS =================
def quick_file_read(file_path):
    """Quick function to read a file and speak it"""
    content = read_any_file(file_path)
    jarvis_read_text(content)

def quick_screen_read():
    """Quick function to read screen and speak it"""
    content = read_screen_once()
    jarvis_read_text(content)

# ================= AGENT INTEGRATION =================
# These functions can be imported and used in your main agent.py file
# Just add the function tools to your agent's tools list

if __name__ == "__main__":
    # Test the functions
    print("🧪 Testing Jarvis Screen Reader...")
    
    # Test screen reading
    print("\n1. Testing screen reading:")
    screen_text = read_screen_once()
    print(f"Screen text: {screen_text[:200]}...")
    
    # Test file reading (if test file exists)
    test_files = ["test.txt", "sample.pdf", "document.docx"]
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n2. Testing file reading ({test_file}):")
            file_content = read_any_file(test_file)
            print(f"File content: {file_content[:200]}...")
            break
    
    # Test supported formats
    print("\n3. Supported formats:")
    print(list_supported_formats_tool())
    
    print("\n✅ Testing complete!")
    print("💡 Usage examples:")
    print("   - quick_screen_read()  # Read and speak screen")
    print("   - quick_file_read('document.txt')  # Read and speak file")
    print("   - read_any_file('file.pdf')  # Read file content")
