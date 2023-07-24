from django.urls import path
from rest_framework.routers import DefaultRouter

from chatbot.views import ChatbotListCreateAPIView, FeedbackCreateAPIView

app_name = "chatbot"

# router = DefaultRouter()
# router.register("", ChatbotQnaApi, basename="Chatbot")

urlpatterns = [
    path(
        "",
        ChatbotListCreateAPIView.as_view(),
        name="Chatbot",
    ),
    path(
        "feedback/",
        FeedbackCreateAPIView.as_view(),
        name="Feedback",
    ),
]

# urlpatterns += router.urls
