# design_agent.py

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

class DesignAgent:
    def __init__(self, config):
        self.output_dir = config.get("output_dir", "./generated_content")
        self.brand_colors = config.get("brand_colors", {
            "background": "#1a1a2e",
            "text_primary": "#ffffff",
            "text_secondary": "#e0e0e0",
            "accent": "#e94560",
            "secondary_bg": "#16213e"
        })
        self.fonts = {
            "bold": config.get("font_bold", "arial.ttf"),
            "regular": config.get("font_regular", "arial.ttf")
        }
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_slide(self, width=1080, height=1080, bg_color=None):
        """Create a blank slide with background"""
        color = bg_color or self.brand_colors["background"]
        img = Image.new("RGB", (width, height), color)
        return img
    
    def add_text(self, img, text, position, font_size=48, 
                 color=None, font_type="bold", max_width=30):
        """Add wrapped text to an image"""
        draw = ImageDraw.Draw(img)
        color = color or self.brand_colors["text_primary"]
        
        try:
            font = ImageFont.truetype(self.fonts[font_type], font_size)
        except OSError:
            font = ImageFont.load_default()
        
        wrapped = textwrap.fill(text, width=max_width)
        draw.multiline_text(position, wrapped, font=font, fill=color, 
                           spacing=10)
        return img
    
    def generate_carousel_images(self, carousel_content, idea_id):
        """Generate all slides for a carousel post"""
        slides = []
        idea_dir = os.path.join(self.output_dir, f"carousel_{idea_id}")
        os.makedirs(idea_dir, exist_ok=True)
        
        # Slide 1: Hook slide
        img = self.create_slide()
        img = self.add_text(
            img, 
            carousel_content["slide_1_hook"],
            position=(80, 350),
            font_size=72,
            color=self.brand_colors["text_primary"]
        )
        if carousel_content.get("slide_1_subtext"):
            img = self.add_text(
                img,
                carousel_content["slide_1_subtext"],
                position=(80, 550),
                font_size=36,
                color=self.brand_colors["text_secondary"],
                font_type="regular"
            )
        
        # Add accent line
        draw = ImageDraw.Draw(img)
        draw.rectangle([80, 300, 300, 305], 
                       fill=self.brand_colors["accent"])
        
        path = os.path.join(idea_dir, "slide_01.png")
        img.save(path, quality=95)
        slides.append(path)
        
        # Content slides
        for i, slide_data in enumerate(carousel_content.get("slides", []), 2):
            img = self.create_slide(
                bg_color=self.brand_colors["secondary_bg"] if i % 2 == 0 
                         else self.brand_colors["background"]
            )
            
            # Slide number
            img = self.add_text(
                img,
                f"{slide_data.get('icon_suggestion', '→')}",
                position=(80, 80),
                font_size=60
            )
            
            # Headline
            img = self.add_text(
                img,
                slide_data["headline"],
                position=(80, 200),
                font_size=56,
                color=self.brand_colors["accent"]
            )
            
            # Body
            img = self.add_text(
                img,
                slide_data["body"],
                position=(80, 380),
                font_size=36,
                color=self.brand_colors["text_secondary"],
                font_type="regular",
                max_width=35
            )
            
            path = os.path.join(idea_dir, f"slide_{i:02d}.png")
            img.save(path, quality=95)
            slides.append(path)
        
        # CTA slide
        img = self.create_slide()
        img = self.add_text(
            img,
            carousel_content.get("slide_final_cta", "Follow for more"),
            position=(80, 380),
            font_size=56,
            color=self.brand_colors["accent"]
        )
        img = self.add_text(
            img,
            "Save this post  •  Share with a friend  •  Follow",
            position=(80, 600),
            font_size=30,
            color=self.brand_colors["text_secondary"],
            font_type="regular"
        )
        
        path = os.path.join(idea_dir, f"slide_final.png")
        img.save(path, quality=95)
        slides.append(path)
        
        return slides