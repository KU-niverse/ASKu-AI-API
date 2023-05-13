from django.urls import path
from rest_framework.routers import DefaultRouter

from chatbot.views import ChatbotListCreateAPIView

app_name = "chatbot"

# router = DefaultRouter()
# router.register("", ChatbotQnaApi, basename="Chatbot")

urlpatterns = [
    path(
        "",
        ChatbotListCreateAPIView.as_view(),
        name="Chatbot",
    ),
]

# urlpatterns += router.urls
