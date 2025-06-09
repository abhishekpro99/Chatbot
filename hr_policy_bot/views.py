import os
import json
import logging
import requests

from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from chatbot_core.chatbot import HRPolicyBot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize HRPolicyBot
bot = HRPolicyBot()

# Microsoft credentials (if needed later for auth)
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
            return JsonResponse({"response": response_text})

        except Exception as e:
            logging.exception("Error in AskEndpoint")
            return JsonResponse({"error": str(e)}, status=500)

# -------------------------------
# Microsoft Bot Framework endpoint (for Teams)
# -------------------------------
@method_decorator(csrf_exempt, name='dispatch')
class BotFrameworkEndpoint(View):
    def post(self, request):
        try:
            body_unicode = request.body.decode("utf-8")
            body = json.loads(body_unicode)

            activity_type = body.get("type", "")
            print(f"👉 Incoming Teams activity type: {activity_type}")

            if activity_type == "message":
                user_input = body.get("text", "")
                activity_id = body.get("id", None)

                print(f"👉 Teams message: '{user_input}'")

                if not user_input.strip():
                    bot_response = "Please enter a valid question about HR policy."
                else:
                    bot_response = bot.chat(user_input)

                reply = {
                    "type": "message",
                    "text": bot_response,
                    "replyToId": activity_id
                }

                print(f"✅ Sending reply: '{bot_response}'")

                return JsonResponse(reply)

            else:
                # For non-message activities, just return 200 OK
                return HttpResponse(status=200)

        except Exception as e:
            logging.exception("Error in BotFrameworkEndpoint")
            return JsonResponse({"error": str(e)}, status=500)
