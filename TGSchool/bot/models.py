from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Question(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='questions/', null=True, blank=True)

    def __str__(self):
        return self.title

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class UserQuestionStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField(null=True, blank=True)
    correct_answers = models.IntegerField(default=0)
    incorrect_answers = models.IntegerField(default=0)
    last_incorrect = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.question.title}"
