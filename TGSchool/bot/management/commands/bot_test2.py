from django.core.management.base import BaseCommand
from django.db import IntegrityError
from telebot import TeleBot, types
from django.conf import settings
from django.contrib.auth.models import User
from bot.models import Question, Answer, IncorrectAnswer, CorrectAnswer  # Додайте CorrectAnswer
import random


class Command(BaseCommand):
    help = 'Запускає Telegram бота'

    def handle(self, *args, **options):
        bot = TeleBot(settings.TELEGRAM_BOT_API_KEY, threaded=False)

        user_states = {}

        @bot.message_handler(commands=['start'])
        def send_welcome(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            tests_button = types.KeyboardButton('Пройти тести')
            markup.add(tests_button)

            user_id = message.from_user.id
            user_name = message.from_user.username

            user_instance, created = User.objects.get_or_create(id=user_id, defaults={'username': user_name})

            bot.send_message(message.chat.id, 'Привіт, ти попав до нашої автошколи. Що ви хочете?', reply_markup=markup)

        @bot.message_handler(func=lambda message: message.text == 'Пройти тести')
        def start_tests(message):
            questions = get_questions_for_user(message.chat.id)
            random.shuffle(questions)

            user_states[message.chat.id] = {
                'questions': questions[:3],
                'current_question_index': 0,
                'answered': False,
            }

            send_question(message.chat.id)

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

                    while len(questions_to_choose_from) < 3:
                        random_question = random.choice(all_questions)
                        if random_question not in questions_to_choose_from:
                            questions_to_choose_from.append(random_question)
                else:
                    questions_to_choose_from = random.sample(all_questions, min(3, len(all_questions)))

                random.shuffle(questions_to_choose_from)

                user_states[message.chat.id] = {
                    'questions': questions_to_choose_from[:3],  # Беремо 3 випадкових питання
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

                question = answer.question  # Отримуємо питання для подальшої логіки

                if answer.is_correct:
                    bot.send_message(chat_id, 'Правильно! 🎉')
                    IncorrectAnswer.objects.filter(telegram_id=chat_id, question=question).delete()

                    # Додаємо правильну відповідь до бази даних
                    if add_correct_answer(chat_id, question):
                        bot.send_message(chat_id, 'Ви часто відповідаєте на це питання правильно!')

                else:
                    correct_answer = question.answers.filter(is_correct=True).first()
                    bot.send_message(chat_id, f'Неправильно. Правильна відповідь: {correct_answer.text}.')
                    IncorrectAnswer.objects.get_or_create(telegram_id=chat_id, question=question)

                user_state['answered'] = True
                bot.edit_message_reply_markup(chat_id, call.message.message_id)
                user_state['current_question_index'] += 1
                send_question(chat_id)

        def add_correct_answer(telegram_id, question):
            # Підрахунок правильних відповідей на конкретне питання для користувача
            correct_count = CorrectAnswer.objects.filter(telegram_id=telegram_id, question=question).count()

            # Якщо користувач відповів правильно на питання тричі
            if correct_count >= 2:  # Тобто, якщо є 2 записи, третя відповідь буде третьою
                # Додаємо новий запис у CorrectAnswer
                CorrectAnswer.objects.create(telegram_id=telegram_id, question=question)
                return True
            return False

        bot.polling(none_stop=True)
