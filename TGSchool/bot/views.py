from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from django.views import View
from django.forms import formset_factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings  # Імпорт налаштувань
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .forms import QuestionForm, AnswerForm, SearchForm
from .models import Question, Registration

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

            if Question.objects.filter(title=title).exists():
                question_form.add_error('title', 'Питання з таким заголовком вже існує.')
                return render(request, 'bot/add_question.html', {
                    'question_form': question_form,
                    'answer_form': answer_formset
                })

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

            if has_answer and has_correct_answer:
                question = question_form.save()
                for answer_form in answer_formset:
                    if answer_form.cleaned_data.get('text'):
                        answer = answer_form.save(commit=False)
                        answer.question = question
                        answer.save()

                messages.success(request, 'Питання та відповіді успішно збережені!')
                return redirect(request.path_info)

        return render(request, 'bot/add_question.html', {
            'question_form': question_form,
            'answer_form': answer_formset
        })

@method_decorator(login_required(login_url='/admin/login/'), name='dispatch')
class CheckRegister(View):
    def get(self, request):
        form = SearchForm()
        registrations = Registration.objects.all()
        return render(request, 'bot/check_register.html', {'form': form, 'registrations': registrations})

    def post(self, request):
        form = SearchForm(request.POST)
        registrations = Registration.objects.all()

        if form.is_valid():
            query = form.cleaned_data['query']
            registrations = registrations.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(email__icontains=query)
            ).distinct()

        return render(request, 'bot/check_register.html', {'form': form, 'registrations': registrations})

@login_required(login_url='/admin/login/')
def delete_registration(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    registration.delete()
    messages.success(request, "Користувача успішно видалено.")
    return redirect('check_register')

@login_required(login_url='/admin/login/')
def send_email(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    subject = "Вітаю, ви записалися на наші курси"
    message = "Вітаємо, {0} {1}!\n\nДякуємо за реєстрацію. Наш менеджер скоро з вами зв'яжеться.".format(
        registration.first_name, registration.last_name
    )
    recipient_list = [registration.email]

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    messages.success(request, f"Лист надіслано на {registration.email}.")
    return redirect('check_register')

class Homepage(LoginRequiredMixin, TemplateView):
    login_url = '/admin/login/'

