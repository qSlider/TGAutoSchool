from django.db import models
from django.contrib.auth.models import User

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

class IncorrectAnswer(models.Model):
    telegram_id = models.BigIntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="incorrect_answers")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telegram ID: {self.telegram_id} - Питання: {self.question.title}"

class CorrectAnswer(models.Model):
    telegram_id = models.BigIntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="correct_answers")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telegram ID: {self.telegram_id} - Питання: {self.question.title}"

class Registration(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

