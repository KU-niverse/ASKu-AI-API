from rest_framework import serializers
from django.db import connection
from datetime import datetime


class ChatbotQnaSerializer(serializers.Serializer):
    """Serializer definition for Chatbot QnA API."""

    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(required=True)
    q_content = serializers.CharField(required=True)
    a_content = serializers.CharField(required=False)
    reference = serializers.CharField(required=False)
    recommended_questions = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    session_id = serializers.IntegerField(required=False)

    class Meta:
        """Meta definition for ChatbotQnaSerializer."""

        fields = [
            "id",
            "session_id",
            "q_content",
            "a_content",
            "reference",
            "recommended_questions",
            "created_at",
            "requested_at",
            "responsed_at",
            "latency_time",
        ]

    def create(self, validated_data):
        session_id = validated_data['session_id']
        created_at = datetime.now()
        q_content = validated_data['q_content']
        a_content = validated_data['a_content']
        reference = validated_data['reference']
        recommended_questions = validated_data['recommended_questions']
        requested_at = validated_data['requested_at']
        responsed_at = validated_data['responsed_at']
        latency_time = validated_data['latency_time']

        with connection.cursor() as cursor:
            sql = """
                INSERT INTO ai_history (
                    session_id, q_content, a_content, reference, created_at, requested_at, responsed_at, latency_time
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = [
                session_id,
                q_content,
                a_content,
                reference,
                created_at,
                requested_at,
                responsed_at,
                latency_time,
            ]
            cursor.execute(sql, values)
        with connection.cursor() as cursor:
            sql = "SELECT id FROM ai_history WHERE session_id = %s AND q_content = %s AND a_content = %s"
            values = [
                session_id,
                q_content,
                a_content,
            ]
            cursor.execute(sql, values)
            chatbot_id = cursor.fetchall()[0][0]
        validated_data['id'] = chatbot_id
        return validated_data
