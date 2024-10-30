from django import forms
from .models import Question, Answer

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'description','image']

class AnswerForm(forms.ModelForm):
    is_correct = forms.BooleanField(required=False, label='Правильна відповідь')

    class Meta:
        model = Answer
        fields = ['text', 'is_correct']

class SearchForm(forms.Form):
    query = forms.CharField(label='Пошук', max_length=100)