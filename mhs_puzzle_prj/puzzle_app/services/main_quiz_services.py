# handle Category score calculation and graph creation 
import json
import base64
from io import BytesIO
import matplotlib.pyplot as plt

from django.db.models import Prefetch
from django.core.cache import cache

from ..models import Question, Category, CategoryResult, Answer

from .graph_services import _draw_life_wheel, _draw_single_gauge
from .recommendation_services import _generate_recommendation

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

        # Serialize all questions into JSON-like structures
        questions_dict = {
            question.id: {
                "alphabetic_id": question.alphabetic_id,
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


    # Set question count
    question_count = len(json.loads(cached_questions) if cached_questions else questions_dict)



_load_questions() 

#TODO Check if the eval function handles all edge cases, particularly missing values.
#executing the functions 
#user is the user object, user_answers is the dictionary {queston id: question score}
# Pass `user_answers` as a dictionary {question_id: score}

def _process_scores(user, user_answers):
    """
    Calculate category scores for a user and generate gauge graphs for display.
    """
    user_data_for_gpt = {} # Dictinary to pass to the Chat GPT recommendation generating function
    gauge_graphs = {}  # Dictionary to store graph images as byte streams
    wheel_of_life = {}  # Dictionary to construct the Wheel of Life later

    #TODO used the _load_questions() func
    # Deserialize cached questions
    cached_questions_data = json.loads(cached_questions) if cached_questions else {}
    category_scores = {}  # Temporary storage for category scores and formulas

    # Prepare category-specific data
    for question_id, data in cached_questions_data.items():
        alphabetic_id = data["alphabetic_id"]
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
            category_scores[category_name]["values"][alphabetic_id] = question_score
    # Process each category's data
    for category_name, category_data in category_scores.items():
        formula = category_data["formula"]
        values = category_data["values"]
        area_name = category_data["area"]

        try:
            # Evaluate the formula
            print(f"The formula is: {formula}")
            print(f"The values to plug into the formula are: {values}")
            category_score = eval(formula, {}, values)
            print(f"the score for the {category_name} category is {category_score}")


            # Save the category score to the database
            try:
                category_obj = Category.objects.get(name=category_name)
                CategoryResult.objects.create(user=user, category=category_obj, score=category_score)
                print("the category score has been successfully saved")
            except Category.DoesNotExist:
                print(f"Category '{category_name}' not found in the database.")
                continue

            if area_name != "Esthetic":
                # Generate and save the gauge graph for the category
                gauge_plot = _draw_single_gauge(round(category_score, 2), category_name)
                gauge_img_bytes = BytesIO()  # Create a byte stream object
                gauge_plot.savefig(gauge_img_bytes, format="jpeg", transparent=True, bbox_inches="tight")
                plt.close(gauge_plot)  # Close the plot to free memory
                gauge_graphs[category_name] = gauge_img_bytes.getvalue()  # Store the byte stream in the cache
                print("the gauge graphs have been constructed successfully")
                # Append the category's name and score to the dictionary used to make the Wheel of Life
                wheel_of_life[category_name] = round(category_score, 2)

        except Exception as e:
            category_score = 50.0
            print(f"Error processing category '{category_name}': {e}")


    # Establish the priority area:
    priority_category = min(wheel_of_life, key=wheel_of_life.get)
    
    print("the priority category is ", priority_category)
    cache.set("user_{user.id}_priority_category", priority_category)

    # Add the necessary data to the dictionary passed later to Chat GPT
    user_data_for_gpt["priority_category"] = priority_category
    user_data_for_gpt["category_scores"] = wheel_of_life

    # Extract answers for questions in the priority category (to avoid passing all the user's answers to Chat GPT, to save tokens :)
    answers_of_priority_category = {}
    for question_id, data in cached_questions_data.items():
        if data["category"] == priority_category and str(question_id) in user_answers:
            print("_process_scores: question of the category identified, passing it to the dictionary to use in recomm generation")
            selected_answer_score = user_answers[str(question_id)]
            selected_answer = next(
                (answer for answer in data["answers"] if answer["score"] == selected_answer_score), None
            )
            if selected_answer:
                answers_of_priority_category[data["content"]] = selected_answer["answer_text"]

    user_data_for_gpt["answers_of_priority_category"] = answers_of_priority_category

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

    print("the data to pass to Chat GPT is ", user_data_for_gpt)

    # Pass the user data to the recommendation-generating function and save the recommendation in cache
    try:
        recommendation = _generate_recommendation(user_data_for_gpt)
    except:
        recommendation = ""
    cache.set(f"user_{user.id}_recommendation", recommendation)

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
 
def _display_priority_category(user_id):
    priority_category_cache_key = "user_{user_id}_priority_category"
    try:
        priority_category = cache.get(priority_category_cache_key)
    except Exception as e:
            print("Error retrieving priority category from cache", e)
            return {"priority_category": "Keep working on your lifestyle"}
    return {"priority_category": priority_category}

def _display_recommendation(user_id):
    recommendation_cache_key = f"user_{user_id}_recommendation"
    try:
        recommendation = cache.get(recommendation_cache_key)
    except Exception as e:
            print("Error retrieving recommendation from cache", e)
            return None
    return {"recommendation": recommendation}
