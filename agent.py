"""
Fixed and cleaned LiveKit worker entrypoint for your Jarvis assistant.

Assumptions:
- The helper modules (jarvis_prompt, jarvis_search, jarvis_get_whether, jarvis_ctrl_window)
  expose the named symbols imported below.
- You have a working LiveKit `livekit` Python package and proper environment variables loaded
  (e.g. LIVEKIT_API_KEY / LIVEKIT_API_SECRET or whatever your deployment requires).

Notes:
- This file focuses on clarity and a safe start/stop sequence for the AgentSession.
- Compatible with latest LiveKit SDK versions (2025+).
"""

import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google, noise_cancellation

# Import your Jarvis modules
from jarvis_prompt import behavior_prompt, Reply_prompts
from jarvis_search import search_internet, get_formatted_datetime
from jarvis_get_whether import get_weather
from jarvis_ctrl_window import (
    shutdown_system,
    restart_system,
    sleep_system,
    create_folder,
    run_application_or_media,
    list_folder_items,
    get_battery_info,
    wifi_status,
    bluetooth_status,
    open_quick_settings,
    open_system_info,
    close_application,
    open_common_app,      
    send_whatsapp_message,    
)

# Load environment variables (your API keys, etc.)
load_dotenv()


class Assistant(Agent):
    """Agent wrapper that provides behavior prompt and tools to the LiveKit agent runtime."""

    def __init__(self) -> None:
        super().__init__(
            instructions=behavior_prompt,
            tools=[
                # Information tools
                search_internet,
                get_formatted_datetime,
                get_weather,

                # System control tools
                shutdown_system,
                restart_system,
                sleep_system,
                create_folder,
                run_application_or_media,
                list_folder_items,
                get_battery_info,
                wifi_status,
                bluetooth_status,
                open_quick_settings,
                open_system_info,
                close_application,
                open_common_app,
                send_whatsapp_message,
            ],
        )


async def entrypoint(ctx: agents.JobContext):
    """Entrypoint for the LiveKit worker.

    The runtime will call this coroutine and provide a JobContext.
    We create an AgentSession configured with a realtime LLM, start it,
    and optionally emit an initial reply. We handle exceptions and ensure
    the session is stopped cleanly.
    """

    session = None
    try:
        # Create an LLM model instance (RealtimeModel from the google plugin)
        llm = google.beta.realtime.RealtimeModel(
            voice="charon",  # change to 'verse' or 'puck' if you prefer
        )
        session = AgentSession(llm=llm)

        # Start the agent session and attach to the room provided by the JobContext
        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

        # Optionally send an initial greeting or reply using your Reply_prompts
        if Reply_prompts:
            await session.generate_reply(instructions=Reply_prompts)

        # Keep the session alive until the job context is cancelled/ends
        await ctx.wait_for_shutdown()

    except asyncio.CancelledError:
        raise  # Graceful shutdown
    except Exception as exc:
        print("[agent.entrypoint] Exception:", type(exc).__name__, exc)
    finally:
        if session is not None:
            try:
                if hasattr(session, "stop"):
                    await session.stop()
                elif hasattr(session, "end"):
                    await session.end()
            except Exception as stop_exc:
                print("[agent.entrypoint] Error stopping session:", stop_exc)


if __name__ == "__main__":
    
    try:
        opts = agents.WorkerOptions(entrypoint=entrypoint)
    except TypeError:
        opts = agents.WorkerOptions(entrypoint_fnc=entrypoint)

    agents.cli.run_app(opts)


