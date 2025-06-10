# hr_policy_bot/views.py

import os
import json
import logging
import asyncio

from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from dotenv import load_dotenv
from chatbot_core.chatbot import HRPolicyBot

# Load environment variables
load_dotenv()

# Initialize HRPolicyBot
bot = HRPolicyBot()

# Microsoft credentials
MS_APP_ID = os.getenv("MicrosoftAppId")
MS_APP_PASSWORD = os.getenv("MicrosoftAppPassword")

# -------------------------------
# Health check endpoint (GET)
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckEndpoint(View):
    def get(self, request):
        return JsonResponse({"status": "UP", "message": "HR Policy Chatbot API is running."})

# -------------------------------
# Ask endpoint (POST API)
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class AskEndpoint(View):
    def post(self, request):
        try:
            body_unicode = request.body.decode("utf-8")
            body = json.loads(body_unicode)
            user_input = body.get("message", "")

            print(f"👉 Received message: '{user_input}'")

            if not user_input.strip():
                return JsonResponse({"error": "Empty message received"}, status=400)

            response_text = bot.chat(user_input)
            print(f"✅ Bot response: '{response_text}'")
            return JsonResponse({"response": response_text})

        except Exception as e:
            logging.exception("Error in AskEndpoint")
            return JsonResponse({"error": str(e)}, status=500)


# -------------------------------
# Microsoft Bot Framework endpoint (for Teams) - FINAL version
# -------------------------------
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter, TurnContext
from botbuilder.schema import Activity

# Initialize adapter
adapter_settings = BotFrameworkAdapterSettings(MS_APP_ID, MS_APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    print(f"⚠️ Exception: {error}")
    await context.send_activity("❗ Sorry, an error occurred. Please try again later.")

adapter.on_turn_error = on_error

@method_decorator(csrf_exempt, name='dispatch')
class BotFrameworkEndpoint(View):
    def post(self, request):
        try:
            body_unicode = request.body.decode("utf-8")
            body = json.loads(body_unicode)
            activity = Activity().deserialize(body)

            print(f"👉 Incoming Teams activity type: {activity.type}")

            async def aux_func(turn_context: TurnContext):
                print(f"👉 TurnContext.activity.type: {turn_context.activity.type}")

                if turn_context.activity.type == "message":
                    user_input = turn_context.activity.text
                    print(f"👉 Teams message: '{user_input}'")

                    try:
                        bot_response = bot.chat(user_input)
                        print(f"✅ Sending reply: '{bot_response}'")
                        await turn_context.send_activity(bot_response)
                    except Exception as e:
                        print(f"❌ Error while generating bot response: {e}")
                        await turn_context.send_activity("❗ Sorry, I could not process your message.")
                else:
                    print(f"Received non-message activity: {turn_context.activity.type}")

            # Run adapter in synchronous event loop to guarantee reply
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            task = loop.create_task(
                adapter.process_activity(
                    activity,
                    request.headers.get("Authorization", ""),
                    aux_func
                )
            )
            loop.run_until_complete(task)
            loop.close()

            # Return 200 OK to Bot Framework (Teams)
            return HttpResponse(status=200)

        except Exception as e:
            logging.exception("Error in BotFrameworkEndpoint")
            return JsonResponse({"error": str(e)}, status=500)
