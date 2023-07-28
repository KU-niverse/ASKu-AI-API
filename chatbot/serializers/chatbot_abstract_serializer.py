from rest_framework import serializers


class ChatbotAbstractSerializer(serializers.Serializer):
    """Serializer definition for Chatbot Abstract API."""

    id = serializers.IntegerField(required=False)
    q_content = serializers.CharField(required=False)
    a_content = serializers.CharField(required=False)
    reference = serializers.CharField(required=False)

    class Meta:
        """Meta definition for ChatbotListSerializer."""

        fields = [
            "id",
            "q_content",
            "a_content",
            "reference",
            "created_at",
        ]

    def create(self, validated_data):
        q_content = validated_data['q_content']
        a_content = validated_data['a_content']
        reference = validated_data['reference']
        created_at = validated_data['created_at']
        return validated_data
