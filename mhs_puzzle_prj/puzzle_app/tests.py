from django.test import TestCase, Client
from django.urls import reverse
from .models import Question, Answer, Category, Area

class QuestionViewTest(TestCase):

    def setUp(self):
        # Create an Area instance for Category's ForeignKey requirement
        self.client = Client()
        self.area = Area.objects.create(
            name="Lifestyle",
            max_score=100.0,
            high_score_good=True,
            formula="(score / max_score) * 100"
        )
        
        # Create a Category linked to the Area
        self.category = Category.objects.create(
            name="Health",
            max_score=100.0,
            high_score_good=True,
            formula="(score / max_score) * 100",
            area=self.area
        )
        
        # Create a few Questions linked to this Category
        self.questions = [
            Question.objects.create(content=f"Question {i}", category=self.category)
            for i in range(3)
        ]
        
        # Create Answer choices for each question
        for question in self.questions:
            Answer.objects.create(question=question, answer_text="Answer 1", score=10)
            Answer.objects.create(question=question, answer_text="Answer 2", score=5)

    def test_question_display_and_progress(self):
        # Test each question display and progress calculation
        for i in range(len(self.questions)):
            response = self.client.get(reverse("quiz"))

            self.assertEqual(response.status_code, 200)
            
            # Check if the question content matches the expected question
            question_data = response.context["question"]
            self.assertEqual(question_data["title"], f"Question {i}")
            
            # Verify the correct category name
            category_name = response.context["category"]
            self.assertEqual(category_name, "Health")
            
            # Check the answer choices for the question
            answer_choices = question_data["answer_choices"]
            self.assertEqual(len(answer_choices), 2)
            self.assertEqual(answer_choices[0]["answer_text"], "Answer 1")
            self.assertEqual(answer_choices[0]["score"], 10)
            self.assertEqual(answer_choices[1]["answer_text"], "Answer 2")
            self.assertEqual(answer_choices[1]["score"], 5)

            # Check the progress percentage
            progress = int(response.context["progress"])
            expected_progress = round((i / len(self.questions)) * 100)
            self.assertEqual(progress, expected_progress)
        
