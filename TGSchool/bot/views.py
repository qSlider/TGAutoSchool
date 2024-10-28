from django.shortcuts import render

from django.http import HttpResponse
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q

from django.http import HttpResponseRedirect
from django.shortcuts import render

from django.shortcuts import render, redirect
from django.views import View
from .forms import QuestionForm, AnswerForm
from django.forms import formset_factory
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Question


@method_decorator(login_required(login_url='/admin/login/'), name='dispatch')
class AddQuestionView(View):
    def get(self, request):
        AnswerFormSet = formset_factory(AnswerForm, extra=6)
        question_form = QuestionForm()
        answer_formset = AnswerFormSet()
        return render(request, 'bot/add_question.html', {
            'question_form': question_form,
            'answer_form': answer_formset
        })

    def post(self, request):
        AnswerFormSet = formset_factory(AnswerForm, extra=6)
        question_form = QuestionForm(request.POST, request.FILES)
        answer_formset = AnswerFormSet(request.POST)

        if question_form.is_valid() and answer_formset.is_valid():
            title = question_form.cleaned_data['title']

            # Перевірка на унікальність заголовка
            if Question.objects.filter(title=title).exists():
                question_form.add_error('title', 'Питання з таким заголовком вже існує.')
                return render(request, 'bot/add_question.html', {
                    'question_form': question_form,
                    'answer_form': answer_formset
                })

            # Перевірка на наявність хоча б однієї відповіді та правильної відповіді
            has_answer = False
            has_correct_answer = False

            for answer_form in answer_formset:
                text = answer_form.cleaned_data.get('text')
                is_correct = answer_form.cleaned_data.get('is_correct')

                if text:
                    has_answer = True
                    if is_correct:
                        has_correct_answer = True
                else:
                    answer_form.add_error('text', 'Це поле обов\'язкове.')

            if not has_answer:
                answer_formset[0].add_error('text', 'Має бути хоча б одна відповідь.')
            elif not has_correct_answer:
                answer_formset[0].add_error('is_correct', 'Має бути хоча б одна правильна відповідь.')

            # Якщо є відповіді та хоча б одна правильна
            if has_answer and has_correct_answer:
                question = question_form.save()
                for answer_form in answer_formset:
                    if answer_form.cleaned_data.get('text'):
                        answer = answer_form.save(commit=False)
                        answer.question = question
                        answer.save()

                # Додаємо повідомлення про успіх
                messages.success(request, 'Питання та відповіді успішно збережені!')
                return redirect(request.path_info)  # Оновлюємо ту ж сторінку

        return render(request, 'bot/add_question.html', {
            'question_form': question_form,
            'answer_form': answer_formset
        })
