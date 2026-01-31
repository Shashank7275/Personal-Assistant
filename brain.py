import sys
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, ChatContext, ChatMessage
from livekit.plugins import google, noise_cancellation
from livekit.plugins.google.realtime import types 

# Import your prompt and tool modules (same as agent.py)
from jarvis_prompt import behavior_prompt, Reply_prompts, get_current_city
from jarvis_search import search_internet, get_formatted_datetime
from jarvis_get_weather import get_weather

from jarvis_ctrl_window import (
    shutdown_system, restart_system, sleep_system, lock_screen, create_folder,
    run_application_or_media, list_folder_items, open_common_app, get_battery_info,
    wifi_status, bluetooth_status, open_quick_settings, open_system_info,
    close_application,
)

from keyboard_mouse_control import (
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
)

load_dotenv()

# ==============================================================================
# CONFIGURATION
# ==============================================================================
instructions_prompt = behavior_prompt  # Use same prompt as agent.py
thinking_capability = []  # Placeholder, replace with actual tool if needed


class MemoryExtractor:
    def __init__(self):
        pass

    async def run(self, chat_ctx):
        # Placeholder for actual memory extraction logic
        print("MemoryExtractor running...")


# ==============================================================================
# ASSISTANT CLASS (Updated with tools from agent.py)
# ==============================================================================
class Assistant(Agent):
    def __init__(self, chat_ctx, current_date: str = None, current_city: str = None) -> None:
        # Format instructions with date and city if provided (like agent.py)
        formatted_instructions = instructions_prompt
        if current_date and current_city:
            formatted_instructions = instructions_prompt.format(
                current_date=current_date,
                current_city=current_city
            )
        
        super().__init__(
            chat_ctx=chat_ctx,
            instructions=formatted_instructions,
            llm=google.beta.realtime.RealtimeModel(voice="Charon"),
            tools=[
                # General Tools
                search_internet,
                get_formatted_datetime,
                get_weather,

                # System Tools
                shutdown_system,
                restart_system,
                sleep_system,
                lock_screen,
                create_folder,
                run_application_or_media,
                list_folder_items,
                open_common_app,
                get_battery_info,
                wifi_status,
                bluetooth_status,
                open_quick_settings,
                open_system_info,
               
               

                # Cursor & Keyboard Inputs
                move_cursor_tool,
                mouse_click_tool,
                scroll_cursor_tool,
                type_text_tool,
                press_key_tool,
                press_hotkey_tool,
                control_volume_tool,
                swipe_gesture_tool,
            ]
        )


# ==============================================================================
# ENTRYPOINT Function (Enhanced with agent.py features)
# ==============================================================================
async def entrypoint(ctx: agents.JobContext):
    session = None
    try:
        # Get current date and city like agent.py
        current_date = await get_formatted_datetime()
        current_city = await get_current_city()

        session = AgentSession(
            llm=google.beta.realtime.RealtimeModel(voice="Charon"),
            preemptive_generation=True,
            allow_interruptions=True,
        )

        # Get current chat context
        current_ctx = session.history.items

        await session.start(
            room=ctx.room,
            agent=Assistant(
                chat_ctx=current_ctx,
                current_date=current_date,
                current_city=current_city
            ),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
                audio_output=types.Modality.AUDIO,  # Enable voice output like agent.py
            ),
        )

        # Greeting logic from agent.py
        hour = datetime.now().hour
        if Reply_prompts:
            greeting = (
                "Good morning!" if 5 <= hour < 12 else
                "Good afternoon!" if 12 <= hour < 18 else
                "Good evening!"
            )
            intro = f"{greeting}\n{Reply_prompts}"
            await session.generate_reply(instructions=intro)

        # Memory extraction
        conv_ctx = MemoryExtractor()
        await conv_ctx.run(current_ctx)

        # Wait for interruption
        await agents.wait_for_interrupt()

    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print("[brain.entrypoint] Exception:", exc)
    finally:
        if session:
            try:
                await session.stop()
            except Exception:
                pass


# ==============================================================================
# MAIN RUNNER
# ==============================================================================
if __name__ == "__main__":
    try:
        opts = agents.WorkerOptions(entrypoint=entrypoint)
    except TypeError:
        # Fallback for older versions (same as agent.py)
        opts = agents.WorkerOptions(entrypoint_fnc=entrypoint)
    agents.cli.run_app(opts)
