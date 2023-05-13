from django.db import models
from django.utils.translation import gettext_lazy as _


class Chatbot(models.Model):
    """Model definition for Chatbot."""

    user = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )  # 사용자
    text = models.TextField(
        null=False,
        blank=False,
        # TODO: required 유효성 검사 추가
    )  # 내용
    data = models.JSONField(
        null=True,
        blank=True,
    )  # gpt3 json
    created_at = models.DateTimeField(
        verbose_name=_("created at"),
        auto_now_add=True,
    )  # Chatbot 레코드가 생성된 일자

    # def __str__(self):
    #     return self.user

    class Meta:
        verbose_name = "Chatbot"
        verbose_name_plural = "Chatbots"
        db_table = "chatbots"
