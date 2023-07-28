from django.urls import path
from rest_framework.routers import DefaultRouter

from chatbot.views import ChatbotListCreateAPIView, FeedbackCreateAPIView, FeedbackCommentCreateAPIView, \
    ChatbotListUpdateAPIView

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
        "<int:user_id>",
        ChatbotListUpdateAPIView.as_view(),
        name="Chatbot",
    ),
    path(
        "feedback/",
        FeedbackCreateAPIView.as_view(),
        name="Feedback",
    ),
    path(
        "feedback/comment",
        FeedbackCommentCreateAPIView.as_view(),
        name="Comment",
    ),
]

# urlpatterns += router.urls
