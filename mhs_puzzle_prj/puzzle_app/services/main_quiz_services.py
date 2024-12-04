# handle Category score calculation and graph creation 
#TODO to pass the question's alphabetic id to the cache and to the _process_scores function
import json
import base64
from io import BytesIO
import matplotlib.pyplot as plt

from django.db.models import Prefetch
from django.core.cache import cache

from ..models import Question, Category, CategoryResult, Answer

from .graph_services import _draw_life_wheel, _draw_single_gauge

def _load_questions():
    ''' Gets quiz questions form cache in the form of a dictionary stored in cached_questions - Prefetch questions and answers, serialize them, and store in Redis. '''
    global question_count, cached_questions

    questions_cache_key = "quiz_questions"

    # Check if questions are already cached
    cached_questions = cache.get(questions_cache_key)

    if not cached_questions:
        # Prefetch questions and answers
        questions = Question.objects.select_related('category', 'category__area').prefetch_related(
            Prefetch('answer_set', queryset=Answer.objects.all())
        )
        print("questions got fetched from the db")

        # Serialize all questions into JSON-like structures
        questions_dict = {
            question.id: {
                "content": question.content,
                "category": question.category.name,
                "formula": question.category.formula,
                "area": question.category.area.name,
                "answers": [
                    {"answer_text": answer.answer_text, "score": answer.score} for answer in question.answer_set.all()
                ],
            }
            for question in questions
        }

        # Cache serialized data
        cache.set(questions_cache_key, json.dumps(questions_dict), timeout=60 * 60 * 24 * 30)  # Cache for 30 days
        print("Questions cached in Redis are ", questions_dict)

    else:
        print("Questions loaded from Redis. The loaded questions are ", cached_questions)

    # Set question count
    question_count = len(json.loads(cached_questions) if cached_questions else questions_dict)
    print("the questions dictionary is")


_load_questions() 

#TODO Check if the eval function handles all edge cases, particularly missing values.
#executing the functions 
#user is the user object, user_answers is the dictionary {queston id: question score}
# Pass `user_answers` as a dictionary {question_id: score}

def _process_scores(user, user_answers):
    """
    Calculate category scores for a user and generate gauge graphs for display.
    """
    gauge_graphs = {}  # Dictionary to store graph images as byte streams
    wheel_of_life = {}  # Dictionary to construct the Wheel of Life later

    # Deserialize cached questions
    cached_questions_data = json.loads(cached_questions) if cached_questions else {}
    category_scores = {}  # Temporary storage for category scores and formulas

    # Prepare category-specific data
    for question_id, data in cached_questions_data.items():
        category_name = data["category"]
        formula = data["formula"]
        area_name = data["area"]

        # Initialize category-specific data if not already present
        if category_name not in category_scores:
            category_scores[category_name] = {
                "formula": formula,
                "area": area_name,
                "values": {}
            }

        # Populate question scores if the user answered this question
        if str(question_id) in user_answers:
            question_score = float(user_answers[str(question_id)])
            category_scores[category_name]["values"][question_id] = question_score

    # Process each category's data
    for category_name, category_data in category_scores.items():
        formula = category_data["formula"]
        values = category_data["values"]
        area_name = category_data["area"]

        try:
            # Evaluate the formula
            category_score = eval(formula, {}, values)

            # Save the category score to the database
            category_obj = Category.objects.get(name=category_name)  # Retrieve the Category instance
            CategoryResult.objects.create(user=user, category=category_obj, score=category_score)

            if area_name != "Esthetic":
                # Generate and save the gauge graph for the category
                gauge_plot = _draw_single_gauge(round(category_score, 2), category_name)
                gauge_img_bytes = BytesIO()  # Create a byte stream object
                gauge_plot.savefig(gauge_img_bytes, format="jpeg", transparent=True, bbox_inches="tight")
                plt.close(gauge_plot)  # Close the plot to free memory
                gauge_graphs[category_name] = gauge_img_bytes.getvalue()  # Store the byte stream in the cache

                # Append the category's name and score to the dictionary used to make the Wheel of Life
                wheel_of_life[category_name] = round(category_score, 2)

        except Exception as e:
            print(f"Error processing category '{category_name}': {e}")

    # Generate the Wheel of Life graph
    print("The data to be used to make the Wheel of Life is the dictionary:", wheel_of_life)
    try:
        wheel_of_life_plot = _draw_life_wheel(wheel_of_life)
        wheel_plot_bytes = BytesIO()
        wheel_of_life_plot.savefig(wheel_plot_bytes, format="jpeg", transparent=True, bbox_inches="tight")
        plt.close(wheel_of_life_plot)
        wheel_of_life_graph = wheel_plot_bytes.getvalue()  # Store the byte stream in the cache
    except Exception as e:
        print(f"Error generating the Wheel of Life graph: {e}")
        wheel_of_life_graph = None

    # Save graphs to cache using user ID
    cache_key_gauge = f"user_{user.id}_gauge_graphs"
    cache.set(cache_key_gauge, gauge_graphs, timeout=60 * 20)  # Store user's gauge graphs in cache for 20 minutes

    if wheel_of_life_graph:
        cache_key_wheel = f"user_{user.id}_wheel_graph"
        cache.set(cache_key_wheel, wheel_of_life_graph, timeout=60 * 20)  # Store user's Wheel of Life in cache for 20 minutes


def _display_graphs(user_id):

    # Retrieve gauge graphs
  
    cache_key_gauge = f"user_{user_id}_gauge_graphs"
    gauge_graphs = cache.get(cache_key_gauge)

    # Prepare data for the template
    gauge_images_data = []  # List to hold image and label pairs
    for label, graph_bytes in gauge_graphs.items():
        # Convert byte data to a base64 string
        img_base64 = base64.b64encode(graph_bytes).decode('utf-8')
        # Append the label and base64 data
        gauge_images_data.append({"label": label, "image": f"data:image/jpeg;base64,{img_base64}"})

    # Retrieve wheel of life graph
    cache_key_wheel = f"user_{user_id}_wheel_graph"

    wheel_of_life_graph_encoded = cache.get(cache_key_wheel)
    if wheel_of_life_graph_encoded:
        try:
           wheel_base64 = base64.b64encode(wheel_of_life_graph_encoded).decode('utf-8')
           wheel_of_life_graph = f"data:image/jpeg;base64,{wheel_base64}"
        except Exception as e:
            print("Error in decoding the wheel of life image", e)

    else:
        print("error in grabbing the encoded wheel image from cache")

    if not gauge_images_data or not wheel_of_life_graph:
        return None

    return {"gauge_images": gauge_images_data, "wheel_image": wheel_of_life_graph}
 
