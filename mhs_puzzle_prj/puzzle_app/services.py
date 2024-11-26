# handle Category score calculation and graph creation 
from django.db.models import Prefetch
from django.http import HttpResponse
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
from io import BytesIO

from .models import Question, Category, CategoryResult, Answer
from django.contrib.auth.models import User

#prep

# Prefetch the querysets globally
def load_questions(): #TODO store it in Redis later
    global questions, question_count, nutrition_questions, categories
    questions = Question.objects.select_related('category', 'category__area').prefetch_related(
        Prefetch('answer_set', queryset=Answer.objects.all())
    )
    categories = Category.objects.all()
    question_count = questions.count()
    nutrition_questions = questions.filter(category__name="Nutrition")  # Questions in the "Nutrition" category


load_questions()
   #prefetch quiz question categories

#executing the functions 
#user is the user object, user_answers is the dictionary {queston id: question score}
# Pass `user_answers` as a dictionary {question_id: score}
def process_scores(user, user_answers):

    gauge_graphs = [] #an awway that holds the variables that refer to the category gauge graphs

    # Iterate over categories to calculate scores
    for category in categories:
        if category.name != "Nutrition":  # Process non-Nutrition categories
            formula = category.formula  # The formula is a string
            values = {}  # Dictionary to hold question alphabetic IDs and their scores
            
            # Collect relevant questions and their scores
            questions_in_category = [q for q in questions if q.category == category]
            for question in questions_in_category:
                question_id_str = str(question.id)
                if question_id_str in user_answers:
                    question_alphabetic_id = question.alphabetic_id
                    score = float(user_answers[question_id_str])  # Convert score to float
                    values[question_alphabetic_id] = score
            
            print(f"Values for category '{category.name}':", values)

            try:
                # Evaluate the formula
                category_score = eval(formula, {}, values)
                print(f"Score for the {category.name} category:", category_score)
                
                # Save the category score to the database
                category_result = CategoryResult.objects.create(user=user, category=category, score=category_score)
                category_result.save()
            
            except Exception as e:
                print(f"Error evaluating formula for category '{category.name}':", e)
                # Log this error in a logging system 

        else:  # Process Nutrition category separately
            formula = "(((whole_grains + legumes + nuts_seeds + vitamin_a_rich_orange_veg + dark_green_leafy_vegetables + other_vegetables + vitamin_a_rich_fruits + citrus + other_fruit) - (soda + max(baked1, baked2, baked3) + other_sweets + processed_meat + max(unprocessed_red_meat_ruminant, unprocessed_red_meat_non_ruminant) + deep_fried_foods + max(instant_noodles,fast_food) + salty_snacks) + 9)/18)*100"
            values = {}

            nutrition_questions = [q for q in questions if q.category == category] #questions is the queryset of all the quesstions, obitained with the load_questions function

            for question in nutrition_questions:
                question_id_str = str(question.id)
                if question_id_str in user_answers:
                    question_alphabetic_id = question.alphabetic_id
                    score = float(user_answers[question_id_str])  # Convert score to float
                    values[question_alphabetic_id] = score

            print(f"Values for Nutrition category:", values)

            try:
                # Evaluate the Nutrition formula
                category_score = eval(formula, {}, values)
                print(f"Score for the Nutrition category:", category_score)
                
                # Save the category score to the database
                category_result = CategoryResult.objects.create(user=user, category=category, score=category_score)
                category_result.save()

                # Build the gauge graph with the category result
                if category.area.name != "Esthetic":
                    draw_simple_gauge #TODO
            
            except Exception as e:
                print(f"Error evaluating formula for Nutrition category:", e)
                # Log this error in a logging system 
    else:
        print("oops there are no answers to evaluate!")
        #log the exception to the logbook

def draw_simple_gauge(user_id, value, label, output_file="gauge.png"):
    """
    Draw a simple gauge chart to represent a percentage value.

    Args:
        value (int or float): The percentage value (0-100) to display on the gauge.
        label (str): The label to display beneath the gauge.
        output_file (str): The file path where the gauge image will be saved.
    """
    # Normalize the value to be between 0 and 100
    value = max(0, min(100, value))

    # Set global font to Georgia
    rcParams['font.family'] = 'Georgia'

    # Create the gauge figure
    fig, ax = plt.subplots(figsize=(4, 2), subplot_kw={'projection': 'polar'})

    # Define the theta range for the gauge
    theta = np.linspace(0, np.pi, 100)
    radius = 1

    # Background arc
    ax.fill_between(theta, 0, radius, color='lightgray', alpha=0.5)

    # Foreground arc
    theta_value = value / 100 * np.pi  # Map value to angle
    ax.fill_between(theta[theta <= theta_value], 0, radius, color='#728bff')

    # Add the percentage label in the center
    ax.text(0, -0.2, f"{value}%", fontsize=20, ha='center', va='center', transform=ax.transAxes)

    # Add the category label below
    ax.text(0, -0.4, label, fontsize=16, ha='center', va='center', transform=ax.transAxes)

    # Customize the chart
    ax.set_theta_zero_location("W")  # Start from the west
    ax.set_theta_direction(-1)  # Clockwise
    ax.set_yticklabels([])  # Remove radial ticks
    ax.set_xticks([])  # Remove angular ticks
    ax.set_frame_on(False)

    # Remove the lower part of the grid (make it appear like a semicircle)
    ax.set_ylim(0, 1)

    # Save the figure to an in-memory buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches="tight", transparent=True)
    buffer.seek(0)
    plt.close(fig)

    # Serve the image as an HTTP response
    return HttpResponse(buffer, content_type="image/png")