from rest_framework import serializers
from django.db import connection


class FeedbackCommentSerializer(serializers.Serializer):
    """Serializer definition for FeedbackComment API."""

    feedback_id = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True)

    class Meta:
        """Meta definition for FeedbackCommentSerializer."""

        fields = [
            "id",
            "feedback_id",
            "content",
        ]

    def create(self, validated_data):
        feedback_id = validated_data['feedback_id']
        content = validated_data['content']
        with connection.cursor() as cursor:
            sql = "INSERT INTO feedback_content (feedback_id, content) VALUES (%s, %s)"
            values = [
                feedback_id,
                content,
            ]
            cursor.execute(sql, values)
        return validated_data
