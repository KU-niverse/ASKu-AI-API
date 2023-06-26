from rest_framework import serializers
from django.db import connection
from datetime import datetime

class ChatbotQnaSerializer(serializers.Serializer):
    """Serializer definition for Chatbot QnA API."""

    session_id = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True)
    reference = serializers.CharField(required=False)

    class Meta:
        """Meta definition for ChatbotQnaSerializer."""

        fields = [
            "id",
            "session_id",
            "content",
            "type",
            "reference",
            "created_at",
        ]

    def create(self, validated_data):
        session_id = validated_data['session_id']
        created_at = datetime.now()
        content = validated_data['content']
        reference = validated_data['reference']
        print(session_id)
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO ai_history (session_id, content, type, reference, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = [
                session_id,
                content,
                True,
                reference,
                created_at,
            ]
            cursor.execute(sql, values)
        return validated_data
