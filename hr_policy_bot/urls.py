# hr_policy_bot/urls.py

from django.urls import path
from django.http import HttpResponse
from .views import BotFrameworkEndpoint, AskEndpoint, HealthCheckEndpoint

urlpatterns = [
    path('', lambda request: HttpResponse("Welcome to HRPolicyBot!")),
    path('api/messages', BotFrameworkEndpoint.as_view(), name="bot_framework_messages"),
    path('ask', AskEndpoint.as_view(), name='ask'),
    path('health', HealthCheckEndpoint.as_view(), name='health_check'),
]
