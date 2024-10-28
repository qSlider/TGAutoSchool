import random

class Quiz:
    def __init__(self):
        self.questions = {
            'Test1': False,
            'Test2': True,
            'Test3': True,
            'Test4': True,
            'Test5': False,
            'Test6': True,
        }
        self.wrong_answers = []  # Список для зберігання неправильних відповідей

    def start_quiz(self):
        print("Починаємо тестування!")
        while True:
            if self.wrong_answers:
                question = self.wrong_answers.pop(0)  # Беремо питання з неправильних
            else:
                question = self.get_random_question()

            answer = self.ask_question(question)

            if answer != self.questions[question]:
                self.wrong_answers.append(question)  # Додаємо неправильну відповідь назад
                print(f"Неправильно. Правильна відповідь: {self.questions[question]}.")
            else:
                print("Правильно! 🎉")

            if not self.more_questions():
                break

        print("Тест завершено! Дякуємо за участь.")

    def get_random_question(self):
        question = random.choice(list(self.questions.keys()))
        return question

    def ask_question(self, question):
        print(f"Питання: {question}. Ваша відповідь (True/False): ", end="")
        user_input = input().strip()
        return user_input.lower() == 'true'

    def more_questions(self):
        response = input("Бажаєте пройти ще один тест? (так/ні): ").strip().lower()
        return response == 'так'

if __name__ == "__main__":
    quiz = Quiz()
    quiz.start_quiz()
