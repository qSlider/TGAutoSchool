from django.core.management.base import BaseCommand
from django.db import IntegrityError
from telebot import TeleBot, types
from django.conf import settings
from django.contrib.auth.models import User
from bot.models import Question, Answer, IncorrectAnswer, Registration
import random


class Command(BaseCommand):
    help = 'Запускає Telegram бота'

    def handle(self, *args, **options):
        bot = TeleBot(settings.TELEGRAM_BOT_API_KEY, threaded=False)

        user_states = {}
        quanity_quiz = 20;

        @bot.message_handler(commands=['start'])
        def send_welcome(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            tests_button = types.KeyboardButton('Пройти тести')
            practice_button = types.KeyboardButton('Записатися на практику')
            markup.add(tests_button, practice_button)

            user_id = message.from_user.id
            user_name = message.from_user.username

            user_instance, created = User.objects.get_or_create(id=user_id, defaults={'username': user_name})

            bot.send_message(message.chat.id, 'Привіт, ти попав до нашої автошколи. Що ви хочете?', reply_markup=markup)

        @bot.message_handler(func=lambda message: message.text == 'Пройти тести')
        def start_tests(message):
            questions = get_questions_for_user(message.chat.id)
            random.shuffle(questions)

            user_states[message.chat.id] = {
                'questions': questions[:quanity_quiz],
                'current_question_index': 0,
                'answered': False,
            }

            send_question(message.chat.id)

        @bot.message_handler(func=lambda message: message.text == 'Записатися на практику')
        def register_user(message):
            bot.send_message(message.chat.id, "Введіть ваше ім'я:")
            bot.register_next_step_handler(message, get_last_name)

        def get_last_name(message):
            first_name = message.text
            bot.send_message(message.chat.id, "Введіть ваше призвіще:")
            bot.register_next_step_handler(message, lambda m: get_phone(m, first_name))

        def get_phone(message, first_name):
            last_name = message.text
            bot.send_message(message.chat.id, "Введіть номер телефону:")
            bot.register_next_step_handler(message, lambda m: get_email(m, first_name, last_name))

        def get_email(message, first_name, last_name):
            phone_number = message.text
            bot.send_message(message.chat.id, "Введіть вашу електронну пошту:")
            bot.register_next_step_handler(message, lambda m: save_registration(m, first_name, last_name, phone_number))

        def save_registration(message, first_name, last_name, phone_number):
            email = message.text
            try:
                registration_instance = Registration(
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    email=email
                )
                registration_instance.save()
                bot.send_message(message.chat.id, "Ваша реєстрація успішна!")
            except Exception as e:
                bot.send_message(message.chat.id, f"Сталася помилка: {str(e)}")

        def get_questions_for_user(telegram_id):
            incorrect_questions = [
                incorrect_answer.question for incorrect_answer in
                IncorrectAnswer.objects.filter(telegram_id=telegram_id)
            ]

            if incorrect_questions:
                return incorrect_questions
            return list(Question.objects.all())

        def send_question(chat_id):
            if chat_id in user_states:
                user_state = user_states[chat_id]
                questions = user_state['questions']
                index = user_state['current_question_index']

                if index < len(questions):
                    question = questions[index]
                    markup = types.InlineKeyboardMarkup()

                    for answer in question.answers.all():
                        markup.add(types.InlineKeyboardButton(answer.text, callback_data=f'answer_{answer.id}'))

                    if question.image:
                        bot.send_photo(chat_id, question.image, caption=f"{question.title}\n\n{question.description}",
                                       reply_markup=markup)
                    else:
                        bot.send_message(chat_id, f"{question.title}\n\n{question.description}", reply_markup=markup)

                    user_state['answered'] = False
                else:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    replay_button = types.KeyboardButton('Пройти ще один тест')
                    markup.add(replay_button)

                    bot.send_message(chat_id, 'Тест завершено! Дякуємо за участь. Хочете пройти ще один тест?',
                                     reply_markup=markup)
                    del user_states[chat_id]
            else:
                bot.send_message(chat_id, 'На жаль, немає більше питань для тестування. Спробуйте пізніше!')

        @bot.message_handler(func=lambda message: message.text == 'Пройти ще один тест')
        def start_new_test(message):
            if message.chat.id not in user_states:
                incorrect_questions = [
                    incorrect_answer.question for incorrect_answer in
                    IncorrectAnswer.objects.filter(telegram_id=message.chat.id)
                ]
                all_questions = list(Question.objects.all())
                if incorrect_questions:
                    questions_to_choose_from = incorrect_questions.copy()

                    while len(questions_to_choose_from) < quanity_quiz:
                        random_question = random.choice(all_questions)
                        if random_question not in questions_to_choose_from:
                            questions_to_choose_from.append(random_question)
                else:
                    questions_to_choose_from = random.sample(all_questions, min(quanity_quiz, len(all_questions)))

                random.shuffle(questions_to_choose_from)

                user_states[message.chat.id] = {
                    'questions': questions_to_choose_from[:quanity_quiz],
                    'current_question_index': 0,
                    'answered': False,
                }

                send_question(message.chat.id)
            else:
                bot.send_message(message.chat.id, 'Ви вже проходите тест. Закінчіть його перед початком нового.')

        @bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
        def handle_answer(call):
            chat_id = call.message.chat.id

            if chat_id in user_states:
                user_state = user_states[chat_id]

                if user_state['answered']:
                    bot.send_message(chat_id, 'Ви вже відповіли на це питання.')
                    return

                answer_id = int(call.data.split('_')[1])
                answer = Answer.objects.get(id=answer_id)

                if answer.is_correct:
                    bot.send_message(chat_id, 'Правильно! 🎉')
                    IncorrectAnswer.objects.filter(telegram_id=chat_id, question=answer.question).delete()
                else:
                    correct_answer = answer.question.answers.filter(is_correct=True).first()
                    bot.send_message(chat_id,
                                     f'Неправильно. Правильна відповідь: {correct_answer.text}.')
                    IncorrectAnswer.objects.get_or_create(telegram_id=chat_id, question=answer.question)

                user_state['answered'] = True
                bot.edit_message_reply_markup(chat_id, call.message.message_id)
                user_state['current_question_index'] += 1
                send_question(chat_id)

        bot.polling(none_stop=True)
