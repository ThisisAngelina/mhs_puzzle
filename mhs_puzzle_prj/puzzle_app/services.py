# handle Category score calculation and graph creation 
from django.db.models import Prefetch
from django.core.cache import cache
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
from io import BytesIO

from .models import Question, Category, CategoryResult, Answer
from django.contrib.auth.models import User

#TODO to refactor to use Redis, just like in views.py
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

#TODO Check if the eval function handles all edge cases, particularly missing values.
#executing the functions 
#user is the user object, user_answers is the dictionary {queston id: question score}
# Pass `user_answers` as a dictionary {question_id: score}
def process_scores(user, user_answers):
    """
    Calculate category scores for a user and generate gauge graphs for display.
    """
    gauge_graphs = {}  # Dictionary to store graph images as byte streams

    # Iterate over categories to calculate scores
    for category in categories:
        formula = category.formula
        values = {}  # Prepare values dictionary for `eval`

        # Filter relevant questions and populate scores
        questions_in_category = [q for q in questions if q.category == category]
        for question in questions_in_category:
            question_id_str = str(question.id)
            if question_id_str in user_answers:
                question_alphabetic_id = question.alphabetic_id
                score = float(user_answers[question_id_str])
                values[question_alphabetic_id] = score

        print(f"Values for category '{category.name}':", values)

        try:
            # Evaluate the formula
            category_score = eval(formula, {}, values)
            print(f"Score for the {category.name} category:", category_score)

            # Save the category score to the database
            CategoryResult.objects.create(user=user, category=category, score=category_score)

            # Generate and save the gauge graph
            gauge_plot = draw_simple_gauge(round(category_score, 2), category.name)
            img_bytes = BytesIO()  # Create a byte stream
            gauge_plot.savefig(img_bytes, format="jpeg", transparent=True, bbox_inches="tight")
            plt.close(gauge_plot)  # Close the plot to free memory
            gauge_graphs[category.name] = img_bytes.getvalue()  # Store the byte stream in the cache

        except Exception as e:
            print(f"Error evaluating formula for category '{category.name}':", e)

    # Save graphs to cache using user ID
    cache_key = f"user_{user.id}_gauge_graphs"
    cache.set(cache_key, gauge_graphs, timeout= 60 * 20)  # store user images for 20 minutes #if the user takes the quiz again, Django automatically overrides the cache so the user will see thier most updated graphs 
    print(f"Cached gauge graphs for user {user.id} under key '{cache_key}'")



def draw_simple_gauge(value, label):
    """
    Draw a simple gauge chart to represent a percentage value.
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

    return fig