import sys
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import google, noise_cancellation
from livekit.plugins.google.realtime import types  # Import types for audio modalities

# Import your prompt and tool modules (ensure correct filenames and locations)
from jarvis_prompt import behavior_prompt, Reply_prompts, get_current_city
from jarvis_search import search_internet, get_formatted_datetime
from jarvis_get_weather import get_weather

from jarvis_ctrl_window import (
    shutdown_system, restart_system, sleep_system, lock_screen, create_folder,
    run_application_or_media, list_folder_items, open_common_app, get_battery_info,
    wifi_status, bluetooth_status, open_quick_settings, open_system_info,
    close_application, open_pdf_in_folder, capture_photo, send_whatsapp_message,
)

from keyboard_mouse_control import (
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool,
    press_key_tool, press_hotkey_tool, control_volume_tool, swipe_gesture_tool,
)

load_dotenv()

# ==============================================================================
# ASSISTANT CLASS
# ==============================================================================
class Assistant(Agent):
    def __init__(self, current_date: str, current_city: str):
        super().__init__(
            instructions=behavior_prompt.format(
                current_date=current_date,
                current_city=current_city
            ),
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
                close_application,
                open_pdf_in_folder,
                capture_photo,

              

                # Cursor & Keyboard Inputs
                move_cursor_tool,
                mouse_click_tool,
                scroll_cursor_tool,
                type_text_tool,
                press_key_tool,
                press_hotkey_tool,
                control_volume_tool,
                swipe_gesture_tool,
            ],
        )

# ==============================================================================
# ENTRYPOINT Function
# ==============================================================================
async def entrypoint(ctx: agents.JobContext):
    session = None
    try:
        current_date = await get_formatted_datetime()
        current_city = await get_current_city()

        llm = google.realtime.RealtimeModel(voice="charon")

        session = AgentSession(
            llm=llm,
            allow_interruptions=True,
        )

        await session.start(
            room=ctx.room,
            agent=Assistant(current_date=current_date, current_city=current_city),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
                audio_output=types.Modality.AUDIO,  # Enable voice output!
            ),
        )

        # Greeting
        hour = datetime.now().hour
        if Reply_prompts:
            greeting = (
                "Good morning!" if 5 <= hour < 12 else
                "Good afternoon!" if 12 <= hour < 18 else
                "Good evening!"
            )
            intro = f"{greeting}\n{Reply_prompts}"
            await session.generate_reply(instructions=intro)  # Will be spoken!

        # Wait for interruption (as per LiveKit agent design)
        await agents.wait_for_interrupt()

    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print("[agent.entrypoint] Exception:", exc)
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
        # Fallback for older versions
        opts = agents.WorkerOptions(entrypoint_fnc=entrypoint)
    agents.cli.run_app(opts)

