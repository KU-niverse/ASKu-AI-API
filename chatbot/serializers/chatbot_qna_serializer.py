from rest_framework import serializers
from chatbot.models import Chatbot
from chatbot.utils import getRelatedDocs, getCompletion

class ChatbotQnaSerializer(serializers.Serializer):
    """Serializer definition for Chatbot QnA API."""

    content = serializers.CharField(required=True)
    reference = serializers.CharField(required=False)

    class Meta:
        """Meta definition for ChatbotQnaSerializer."""

        model = Chatbot
        fields = [
            "id",
            "session_id",
            "content",
            "type",
            "reference",
            "created_at",
        ]

    def create(self, validated_data):
        return Chatbot.objects.create(**validated_data)
