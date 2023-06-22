from rest_framework import serializers
from chatbot.models import Chatbot
from chatbot.utils import getRelatedDocs, getCompletion

class ChatbotQnaSerializer(serializers.Serializer):
    """Serializer definition for Chatbot QnA API."""

    text = serializers.CharField(required=True)
    answer = serializers.SerializerMethodField()

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

    extra_kwargs = {
        "text": {"required": True},
    }

    def create(self, validated_data):
        return Chatbot.objects.create(**validated_data)

    def get_answer(self, obj):
        try:
            user_question = obj.text
            Completion = getCompletion(user_question, getRelatedDocs(user_question, database="Redis"))
            assistant_content = Completion[-1]['content']['choices'][0]['message']['content']
            return assistant_content
        except:
            return False

