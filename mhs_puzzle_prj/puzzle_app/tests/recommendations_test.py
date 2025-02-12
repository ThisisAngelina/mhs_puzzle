from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.utils.html import escape
import markdown
from puzzle_app.services.recommendation_services import _generate_recommendation  # Adjust the import based on your project structure

class GenerateRecommendationTest(TestCase):

    @patch("openai.chat.completions.create")  # Mock OpenAI API call
    def test_generate_recommendation(self, mock_openai):
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "## Recommendation\n- Improve sleep\n- Reduce stress"

        mock_openai.return_value = mock_response  # Set mock return value

        # Test input data
        user_data = {
            "priority_category": "sleep",
            "category_scores": {"sleep": 40.0, "stress": 60.0},
            "answers_of_priority_category": {"How many hours do you sleep?": "5 hours"}
        }

        # Call the function
        result = _generate_recommendation(user_data)

        # Expected markdown conversion
        expected_html = markdown.markdown("## Recommendation\n- Improve sleep\n- Reduce stress")

        # Assertions
        self.assertEqual(result, expected_html)  # Ensure HTML output matches expected result
        self.assertIn("<h2>Recommendation</h2>", result)  # Ensure Markdown was converted to HTML
        self.assertIn("<ul>", result)  # Ensure the bullet points were converted correctly
        self.assertTrue(mock_openai.called)  # Ensure OpenAI API was called