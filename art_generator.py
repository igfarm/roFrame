#!/usr/bin/env python3

import random
from PIL import Image, ImageDraw
import io
import base64

def generate_mondrian(width=1024, height=600):
    """
    Generates a Piet Mondrian-style image of size (width x height).
    Returns the result as a base64 encoded GIF image.
    """

    # Create a new white background image
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Number of randomly placed vertical and horizontal lines
    num_vertical_lines = random.randint(3, 5)
    num_horizontal_lines = random.randint(2, 4)

    # Randomly generate line positions (excluding outer edges to avoid duplication)
    # We will add the outer edges (0 and width/height) to the list to form grid boundaries
    vertical_lines = sorted(
        random.sample(range(100, width - 100), num_vertical_lines)
    )
    horizontal_lines = sorted(
        random.sample(range(100, height - 100), num_horizontal_lines)
    )

    # Include the extreme edges for the grid
    vertical_lines = [0] + vertical_lines + [width]
    horizontal_lines = [0] + horizontal_lines + [height]

    # Define a palette of colors typical of Mondrian
    # White, Red, Blue, Yellow
    palette = [
        (255, 255, 255),   # White
        (237, 28, 36),     # Red
        (63, 72, 204),     # Blue
        (255, 242, 0)      # Yellow
    ]
    # Weights for how often each color is chosen (e.g., more white space)
    # Adjust to taste
    weights = [0.6, 0.15, 0.15, 0.1]

    # Iterate over the grid cells defined by our lines
    for i in range(len(vertical_lines) - 1):
        for j in range(len(horizontal_lines) - 1):
            left = vertical_lines[i]
            right = vertical_lines[i + 1]
            top = horizontal_lines[j]
            bottom = horizontal_lines[j + 1]

            # Randomly pick a color for this cell
            fill_color = random.choices(palette, weights=weights, k=1)[0]

            # Fill the cell with the chosen color
            draw.rectangle([left, top, right, bottom], fill=fill_color)

    # Now draw the black grid lines on top
    line_thickness = random.choice([4, 6, 8])  # or pick a fixed thickness
    black = (0, 0, 0)

    # Draw vertical lines
    for x in vertical_lines:
        draw.line([(x, 0), (x, height)], fill=black, width=line_thickness)
    # Draw horizontal lines
    for y in horizontal_lines:
        draw.line([(0, y), (width, y)], fill=black, width=line_thickness)

    # Save the image to a bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format="GIF")
    buffer.seek(0)

    # Encode the image to base64
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    # Return the base64 string
    return f"data:image/gif;base64,{img_base64}"

if __name__ == "__main__":
    img_tag = f'<img src="{generate_mondrian()}" alt="Mondrian-style art">'
    print(img_tag)
