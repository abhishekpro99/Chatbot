# bot_app.py

import os
import sys
import asyncio
from aiohttp import web
from dotenv import load_dotenv

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    BotFrameworkAdapter,
    TurnContext,
)
from botbuilder.schema import Activity, ActivityTypes

# Load env vars
load_dotenv()

# Import HRPolicyBot
sys.path.append(os.path.abspath("./"))
from chatbot_core.chatbot import HRPolicyBot

# Initialize HRPolicyBot
bot = HRPolicyBot()

# Microsoft App credentials
APP_ID = os.getenv("MicrosoftAppId", "")
APP_PASSWORD = os.getenv("MicrosoftAppPassword", "")

# Adapter settings
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    print(f"⚠️ Exception: {error}")
    await context.send_activity("❗ Sorry, an error occurred. Please try again later.")

ADAPTER.on_turn_error = on_error

# Bot message handler
async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)

    async def aux_func(turn_context: TurnContext):
        if activity.type == ActivityTypes.message:
            user_input = activity.text
            print(f"👉 Teams message: '{user_input}'")

            bot_response = bot.chat(user_input)
            print(f"✅ Sending reply: '{bot_response}'")

            await turn_context.send_activity(bot_response)
        else:
            print(f"Received non-message activity: {activity.type}")

    await ADAPTER.process_activity(activity, "", aux_func)
    return web.Response(status=200)

# --------------------------------------
# Mount Django WSGI app inside aiohttp
# --------------------------------------
# Setup Django
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hr_policy_bot_project.settings")

import django
from django.core.handlers.wsgi import WSGIHandler
django.setup()

# Create Django app
django_app = WSGIHandler()

# aiohttp_wsgi wrapper
from aiohttp_wsgi import WSGIHandler as AiohttpWSGIHandler

# Start aiohttp app
app = web.Application()

# Add bot endpoint
app.router.add_post("/api/messages", messages)

# Mount Django for other routes
django_handler = AiohttpWSGIHandler(django_app)

# You can add exact routes or catch all if you want
app.router.add_route("*", "/ask", django_handler)
app.router.add_route("*", "/health", django_handler)
app.router.add_route("*", "/", django_handler)

# Run server
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8000))
    print(f"Bot + Django is running on port {PORT}")
    web.run_app(app, port=PORT)
