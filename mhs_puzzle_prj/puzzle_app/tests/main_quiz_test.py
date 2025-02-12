from django.test import TestCase, override_settings
from django.core.cache import cache
import json

from django.contrib.auth.models import User
from puzzle_app.models import Question, Category, Area, CategoryResult, Answer
from puzzle_app.services.main_quiz_services import _process_scores, _load_questions, _display_priority_category, _display_recommendation


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  # Don't forget to activate redis
    }
})
class ProcessScoresRedisTest(TestCase):
    
    def setUp(self):
        """Set up test data and Redis cache."""
        # Clear cache before running the test
        cache.clear()

        # Create mock user
        self.user = User.objects.create(id=1, username="test_user")

        # Create mock area and category
        self.area = Area.objects.create(id=1, name="Health", formula="", max_score=100)
        self.category = Category.objects.create(
            id=1, area=self.area, name="Sleep", formula="(Q1 + Q2) / 2", max_score=100
        )

        # Create mock questions
        self.question1 = Question.objects.create(
            id=1, alphabetic_id="Q1", content="How many hours do you sleep?", category=self.category
        )
        self.question2 = Question.objects.create(
            id=2, alphabetic_id="Q2", content="Do you wake up refreshed?", category=self.category
        )

        # Create mock answers
        Answer.objects.create(question=self.question1, answer_text="Less than 5", score=20)
        Answer.objects.create(question=self.question1, answer_text="5-7", score=50)
        Answer.objects.create(question=self.question1, answer_text="More than 7", score=100)

        Answer.objects.create(question=self.question2, answer_text="No", score=30)
        Answer.objects.create(question=self.question2, answer_text="Sometimes", score=60)
        Answer.objects.create(question=self.question2, answer_text="Yes", score=90)

        # Mock quiz questions and store them in Redis cache
        self.mock_cached_questions = {
            "1": {
                "alphabetic_id": "Q1",
                "content": "How many hours do you sleep?",
                "category": "Sleep",
                "formula": "(Q1 + Q2) / 2",
                "area": "Health",
                "answers": [
                    {"answer_text": "Less than 5", "score": 20},
                    {"answer_text": "5-7", "score": 50},
                    {"answer_text": "More than 7", "score": 100}
                ],
            },
            "2": {
                "alphabetic_id": "Q2",
                "content": "Do you wake up refreshed?",
                "category": "Sleep",
                "formula": "(Q1 + Q2) / 2",
                "area": "Health",
                "answers": [
                    {"answer_text": "No", "score": 30},
                    {"answer_text": "Sometimes", "score": 60},
                    {"answer_text": "Yes", "score": 90}
                ],
            },
        }

        cache.set("quiz_questions", json.dumps(self.mock_cached_questions), timeout=60 * 60)
        _load_questions()
    

    def test_process_scores(self):
        """Test `_process_scores()`."""
        # Simulated user answers
        user_answers = {"1": 50, "2": 90}
        # Call function
        _process_scores(self.user, user_answers)

        # Check if the category score was saved in the database
        category_result = CategoryResult.objects.filter(user=self.user, category=self.category).first()
        self.assertIsNotNone(category_result)
        self.assertEqual(category_result.score, 70.0)  # Expected avg (50+90)/2
    '''
    def test_display_priority_category(self):
        """Test _display_priority_category """
        priority_category = _display_priority_category(self.user.id)
        self.assertEqual(priority_category, "Sleep")
        '''

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()