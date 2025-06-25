# hr_policy_bot/views.py

import os
import json
import logging
import asyncio
import aiohttp
import requests


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
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

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

# -----------------------------
# Get Microsoft Teams user's email using Graph API
# -----------------------------
def get_user_email_from_graph(aad_object_id: str) -> str:
    try:
        # Get an access token for Microsoft Graph using client credentials
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default"
        }
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        access_token = token_json.get("access_token")
        if not access_token:
            logging.error("❌ Failed to get access token for Graph API.")
            return None

        # Call Graph API to get user profile
        graph_url = f"https://graph.microsoft.com/v1.0/users/{aad_object_id}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(graph_url, headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            return user_data.get("mail") or user_data.get("userPrincipalName")
        else:
            logging.warning(f"⚠️ Graph API returned error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logging.error(f"❌ Error fetching email: {e}")
        return None


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

                     # Fetch user AAD object ID
                    user_aad_object_id = turn_context.activity.from_property.aad_object_id
                    user_email = get_user_email_from_graph(user_aad_object_id)
                    print(f"📧 User email: {user_email}")

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
