from django.core.management.base import BaseCommand
from django.db import IntegrityError
from telebot import TeleBot, types
from django.conf import settings
from django.contrib.auth.models import User
from bot.models import Question, Answer, UserQuestionStats
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
            questions = list(Question.objects.all())
            random.shuffle(questions)

            user_states[message.chat.id] = {
                'questions': questions[:3],
                'current_question_index': 0,
                'answered': False,
            }

            send_question(message.chat.id)

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

                    bot.send_message(chat_id, 'Тест завершено! Дякуємо за участь. Хочете пройти ще один тест?', reply_markup=markup)
                    del user_states[chat_id]
            else:
                bot.send_message(chat_id, 'На жаль, немає більше питань для тестування. Спробуйте пізніше!')

        @bot.message_handler(func=lambda message: message.text == 'Пройти ще один тест')
        def start_new_test(message):
            questions = list(Question.objects.all())
            random.shuffle(questions)

            user_states[message.chat.id] = {
                'questions': questions[:3],
                'current_question_index': 0,
                'answered': False,
            }

            send_question(message.chat.id)

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
                user = call.from_user

                user_instance = User.objects.filter(id=user.id).first()
                if user_instance is None:
                    bot.send_message(chat_id, 'Користувач не знайдений у системі. Не вдалося зберегти статистику.')
                    return


                stat, created = UserQuestionStats.objects.get_or_create(user=user_instance, question=answer.question)
                if answer.is_correct:
                    bot.send_message(chat_id, 'Правильно! 🎉')
                    stat.correct_answers += 1
                else:
                    correct_answer = answer.question.answers.filter(is_correct=True).first()
                    bot.send_message(chat_id,
                                     f'Неправильно. Правильна відповідь: {correct_answer.text}.')
                    stat.incorrect_answers += 1

                stat.save()
                user_state['answered'] = True
                bot.edit_message_reply_markup(chat_id, call.message.message_id)
                user_state['current_question_index'] += 1
                send_question(chat_id)

        bot.polling(none_stop=True)
