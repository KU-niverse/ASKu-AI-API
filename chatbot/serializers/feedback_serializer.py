from rest_framework import serializers
from django.db import connection
from datetime import datetime


class FeedbackSerializer(serializers.Serializer):
    """Serializer definition for Feedback API."""

    qna_id = serializers.IntegerField(required=True)
    feedback = serializers.BooleanField(required=True)

    class Meta:
        """Meta definition for FeedbackSerializer."""

        fields = [
            "id",
            "qna_id",
            "feedback",
        ]

    def create(self, validated_data):
        qna_id = validated_data['qna_id']
        feedback = validated_data['feedback']
        # created_at = datetime.now()
        with connection.cursor() as cursor:
            sql = "INSERT INTO feedback (qna_id, feedback) VALUES (%s, %s)"
            values = [
                qna_id,
                feedback,
            ]
            cursor.execute(sql, values)
        return validated_data
