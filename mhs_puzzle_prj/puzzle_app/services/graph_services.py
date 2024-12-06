# graph drawing functionality

import matplotlib
matplotlib.use("Agg") # need to set a non-GUI matplotlib backend to prevent threading issues
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np



def _draw_single_gauge(value, label): 
    ''' Draws one gauge graph (per category) '''
   
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


def _draw_life_wheel(wheel_of_life_data): 
    ''' Draws a sigle graph that contains all the categories. '''
    # The input is a dict that looks like {'category_name': category_score} 

    if not wheel_of_life_data:
        raise ValueError("Wheel of Life data is empty.")

    categories = list(wheel_of_life_data.keys())
    scores = list(wheel_of_life_data.values())

    # Ensure the wheel is circular by repeating the first category and score at the end
    categories.append(categories[0])  # Close the loop for categories
    scores.append(scores[0])  # Close the loop for scores

    # Number of categories
    num_categories = len(categories) - 1  # Exclude the duplicate for counting ticks

    # Create the figure and polar subplot
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})

    # Set the angles for each category
    angles = np.linspace(0, 2 * np.pi, len(categories))

    # Plot the data as a closed polygon
    ax.fill(angles, scores, color="#728bff", alpha=0.25)
    ax.plot(angles, scores, color="#728bff", linewidth=2)

    # Add gridlines and labels
    ax.set_yticks(range(1, 11))  # Set radial ticks for scores (1 to 10)
    ax.set_yticklabels([''] * 10)  # Set radial tick labels to empty strings to remove them
    ax.set_xticks(angles[:-1])  # Exclude the duplicated angle for ticks
    ax.set_xticklabels(categories[:-1], fontsize=12, fontweight="bold")  # Exclude duplicate category for labels

    # Add a title
    ax.set_title("Wheel of Life", va="bottom", fontsize=14, fontweight="bold")

    # Style the grid
    ax.grid(color="gray", linestyle="--", linewidth=0.5)
    ax.spines["polar"].set_visible(False)  # Remove the polar frame

    return fig
