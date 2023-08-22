from rest_framework import serializers
from django.db import connection
from datetime import datetime


class ChatbotQnaSerializer(serializers.Serializer):
    """Serializer definition for Chatbot QnA API."""

    user_id = serializers.IntegerField(required=True)
    q_content = serializers.CharField(required=True)
    a_content = serializers.CharField(required=False)
    reference = serializers.CharField(required=False)
    session_id = serializers.IntegerField(required=False)

    class Meta:
        """Meta definition for ChatbotQnaSerializer."""

        fields = [
            "id",
            "session_id",
            "q_content",
            "a_content",
            "reference",
            "created_at",
        ]

    def create(self, validated_data):
        session_id = validated_data['session_id']
        created_at = datetime.now()
        q_content = validated_data['q_content']
        a_content = validated_data['a_content']
        reference = validated_data['reference']
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO ai_history (session_id, q_content, a_content, reference, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = [
                session_id,
                q_content,
                a_content,
                reference,
                created_at,
            ]
            cursor.execute(sql, values)
        return validated_data
