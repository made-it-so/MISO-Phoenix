from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import os

def create_challenge_image(filename="challenge.jpg"):
    # 1. Create a chaotic background
    width, height = 800, 400
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Draw random noise (The "Static")
    for _ in range(5000):
        x, y = random.randint(0, width), random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)))

    # Draw distracting lines (The "Interference")
    for _ in range(50):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(200, 200, 200), width=2)

    # 2. Embed the Secret Instruction (The "Signal")
    # We use basic drawing because we assume no external fonts are installed on the minimal server
    # Text: "PROJECT OMEGA: STATUS CRITICAL"
    text_color = (0, 0, 0)
    
    # We simulate text by drawing it (since default font is tiny)
    # Or we try to load a default, falling back to simple drawing
    try:
        # Try to use a large font if available
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        draw.text((50, 150), "PROJECT OMEGA", font=font, fill=text_color)
        draw.text((50, 220), "STATUS: CRITICAL", font=font, fill=(255, 0, 0))
        draw.text((50, 290), "CODE: 99-ALPHA-ZULU", font=font, fill=(0, 0, 255))
    except IOError:
        # Fallback for minimal container: Draw it manually or use default
        draw.text((50, 150), "PROJECT OMEGA (Vision Test)", fill=text_color)
        draw.text((50, 170), "STATUS: CRITICAL", fill=text_color)
        draw.text((50, 190), "CODE: 99-ALPHA-ZULU", fill=text_color)

    # 3. Apply Blur (The "Fog")
    image = image.filter(ImageFilter.GaussianBlur(1))
    
    # Save
    image.save(filename, quality=95)
    print(f"Generated {filename}")

if __name__ == "__main__":
    create_challenge_image()
