from django.urls import path

from chatbot.views import ChatbotCreateAPIView, ChatbotListUpdateAPIView, \
    FeedbackCreateAPIView, FeedbackCommentCreateAPIView

app_name = "chatbot"

urlpatterns = [
    path(
        "",
        ChatbotCreateAPIView.as_view(),
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
