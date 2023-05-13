from rest_framework import serializers
from chatbot.models import Chatbot

class ChatbotQnaSerializer(serializers.Serializer):
    """Serializer definition for Chatbot QnA API."""

    text = serializers.CharField(required=True)

    class Meta:
        """Meta definition for ChatbotQnaSerializer."""

        model = Chatbot
        fields = [
            "id",
            "user",
            "text",
            "data",
            "created_at",
        ]
    #
    #     read_only_fields = [
    #         # "id",
    #         # "created_at",
    #         # "updated_at",
    #     ]

    extra_kwargs = {
        "text": {"required": True},
    }

    def create(self, validated_data):
        return Chatbot.objects.create(**validated_data)
