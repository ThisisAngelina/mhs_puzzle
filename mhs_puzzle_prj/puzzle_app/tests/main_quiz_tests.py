import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache

from ..models import Area, Category, Question, Answer, CategoryResult
from ..services.main_quiz_services import _load_questions, _process_scores, _display_graphs


class MainQuizServicesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')

        # Create test area, category, questions, and answers
        self.area = Area.objects.create(name='Lifestyle', max_score=100, high_score_good=True, formula='A + B')
        self.category = Category.objects.create(
            area=self.area, name='Health', max_score=100, high_score_good=True, formula='A + B'
        )
        self.question1 = Question.objects.create(category=self.category, alphabetic_id='A', content='Question 1')
        self.question2 = Question.objects.create(category=self.category, alphabetic_id='B', content='Question 2')
        self.answer1 = Answer.objects.create(question=self.question1, answer_text='Answer 1', score=10)
        self.answer2 = Answer.objects.create(question=self.question2, answer_text='Answer 2', score=20)

        # Simulate the cache
        questions_dict = {
            str(self.question1.id): {
                'id': self.question1.id,
                'category': self.category.name,  # Explicitly match Category.name
                'formula': self.category.formula,
                'alphabetic_id': self.question1.alphabetic_id,
                'content': self.question1.content,
                'area': self.area.name,
                'answers': [
                    {'id': self.answer1.id, 'answer_text': self.answer1.answer_text, 'score': self.answer1.score}
                ]
            },
            str(self.question2.id): {
                'id': self.question2.id,
                'category': self.category.name,  # Explicitly match Category.name
                'formula': self.category.formula,
                'alphabetic_id': self.question2.alphabetic_id,
                'content': self.question2.content,
                'area': self.area.name,
                'answers': [
                    {'id': self.answer2.id, 'answer_text': self.answer2.answer_text, 'score': self.answer2.score}
                ]
            }
        }
        cache.set('quiz_questions_test', json.dumps(questions_dict), timeout=60 * 5)  # Cache for 5 minutes

    def test_load_questions(self):
        _load_questions()
        questions_cache = cache.get('quiz_questions_test')
        self.assertIsNotNone(questions_cache)
        questions_dict = json.loads(questions_cache)
        self.assertEqual(len(questions_dict), 2)
        self.assertIn(str(self.question1.id), questions_dict)
        self.assertIn(str(self.question2.id), questions_dict)

    def test_process_scores(self):
        user_answers = {str(self.question1.id): 10, str(self.question2.id): 20}
        _process_scores(self.user, user_answers)
        
        # Validate CategoryResult
        category_result = CategoryResult.objects.get(user=self.user, category=self.category)
        self.assertEqual(category_result.score, 30)

        # Validate Gauge Graphs
        cache_key_gauge = f"user_{self.user.id}_gauge_graphs"
        gauge_graphs = cache.get(cache_key_gauge)
        self.assertIsNotNone(gauge_graphs)
        self.assertIn('Health', gauge_graphs)

    def test_display_graphs(self):
        user_answers = {str(self.question1.id): 10, str(self.question2.id): 20}
        _process_scores(self.user, user_answers)

        # Retrieve graphs
        graphs = _display_graphs(self.user.id)
        self.assertIsNotNone(graphs)
        self.assertIn('gauge_images', graphs)
        self.assertIn('wheel_image', graphs)
        self.assertTrue(len(graphs['gauge_images']) > 0)