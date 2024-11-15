from django.test import TestCase, Client
from django.urls import reverse
from .models import Question, Answer, Category, Area, QuestionResult
from django.contrib.auth.models import User


class QuizViewTests(TestCase):
    def setUp(self):
        # Set up the database objects
        self.client = Client()

        # Create a test user
        self.user = User.objects.create_user(username="test_user", password="password")

        # Create an area and category
        self.area = Area.objects.create(name="General Knowledge", max_score=100, high_score_good=True, formula="simple")
        self.category = Category.objects.create(name="Nutrition", area=self.area, max_score=50, high_score_good=True, formula="nutrition_formula")
        
        # Create questions and answers
        self.question1 = Question.objects.create(category=self.category, content="What is your favorite fruit?")
        self.question2 = Question.objects.create(category=self.category, content="Do you eat vegetables daily?")
        self.answer1 = Answer.objects.create(question=self.question1, answer_text="Apple", score=10)
        self.answer2 = Answer.objects.create(question=self.question1, answer_text="Banana", score=5)
        self.answer3 = Answer.objects.create(question=self.question2, answer_text="Yes", score=20)
        self.answer4 = Answer.objects.create(question=self.question2, answer_text="No", score=0)

        # URL for the quiz view
        self.quiz_url = reverse('quiz')  # Replace 'quiz' with the actual name of the view in your URLs.

    def test_get_quiz_initial_display(self):
        # Test the initial display of the quiz
        response = self.client.get(self.quiz_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'puzzle_app/question.html')
        self.assertIn("progress", response.context)
        self.assertIn("question", response.context)
        self.assertEqual(response.context["question"]["title"], "What is your favorite fruit?")

    def test_get_quiz_with_nutrition_questions(self):
        # Simulate moving to the "Nutrition" category
        session = self.client.session
        session['current_question_index'] = 1
        session.save()

        response = self.client.get(self.quiz_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("nutrition_questions", response.context)
        nutrition_questions = response.context["nutrition_questions"]
        self.assertEqual(len(nutrition_questions), 2)  # All nutrition questions should be displayed
        self.assertEqual(nutrition_questions[0]["title"], "What is your favorite fruit?")
        self.assertEqual(nutrition_questions[1]["title"], "Do you eat vegetables daily?")

    def test_post_quiz_submit_valid_answer(self):
        # Test submitting a valid answer
        session = self.client.session
        session['current_question_index'] = 0
        session.save()

        response = self.client.post(self.quiz_url, {
            "selected_score_{}".format(self.question1.id): self.answer1.score,
        })
        self.assertRedirects(response, self.quiz_url)

        # Check that the answer is saved in the database
        result = QuestionResult.objects.filter(user=self.user, question=self.question1).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.score, self.answer1.score)

    def test_post_quiz_submit_no_answer(self):
        # Test submitting without selecting an answer
        session = self.client.session
        session['current_question_index'] = 0
        session.save()

        response = self.client.post(self.quiz_url, {
            "selected_score_{}".format(self.question1.id): "",
        })
        self.assertRedirects(response, self.quiz_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ooops, please select an answer!")

    def test_reset_index_after_all_questions(self):
        # Simulate answering the last question
        session = self.client.session
        session['current_question_index'] = 2
        session.save()

        response = self.client.get(self.quiz_url)
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertEqual(session['current_question_index'], 0)  # Index should reset after all questions are done