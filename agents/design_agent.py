# design_agent.py

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# Brand-safe palette rotation so consecutive carousels don't look identical.
# Each: (bg_top, bg_bottom, accent, text, text_secondary). Dark, high-contrast.
PALETTES = [
    ("#1a1a2e", "#16213e", "#e94560", "#ffffff", "#cfd3e0"),  # original navy/red
    ("#0f2027", "#203a43", "#36d1dc", "#ffffff", "#c9e9ee"),  # teal deep
    ("#2b1055", "#7597de", "#ffd166", "#ffffff", "#e7e0ff"),  # violet/gold
    ("#231526", "#3a1c4a", "#ff6b9d", "#ffffff", "#f0d9e8"),  # plum/pink
    ("#13293d", "#006494", "#f9c74f", "#ffffff", "#cfe6f2"),  # ocean/amber
    ("#1b1b2f", "#162447", "#1f4068", "#ffffff", "#c7cddb"),  # midnight
]


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


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
        self.handle = config.get("instagram_handle", "")
        os.makedirs(self.output_dir, exist_ok=True)

    def add_footer(self, img, page_num, total_pages):
        """Brand handle bottom-left, page counter bottom-right — on every slide."""
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(self.fonts["regular"], 28)
        except OSError:
            font = ImageFont.load_default(size=28)
        color = self.brand_colors["text_secondary"]
        y = img.height - 70
        if self.handle:
            draw.text((80, y), self.handle, font=font, fill=color)
        counter = f"{page_num}/{total_pages}"
        w = draw.textlength(counter, font=font)
        draw.text((img.width - 80 - w, y), counter, font=font, fill=color)
        return img
    
    def _gradient(self, top, bottom, width, height):
        """Vertical two-colour gradient background."""
        t, b = _hex(top), _hex(bottom)
        base = Image.new("RGB", (1, height))
        px = base.load()
        for y in range(height):
            f = y / max(height - 1, 1)
            px[0, y] = tuple(int(t[i] + (b[i] - t[i]) * f) for i in range(3))
        return base.resize((width, height))

    def create_slide(self, width=1080, height=1080, bg_color=None, palette=None, shapes=True):
        """Slide background: gradient from the palette + soft accent blobs.
        Falls back to a flat colour if bg_color is forced (legacy callers)."""
        if bg_color and not palette:
            return Image.new("RGB", (width, height), bg_color)
        p = palette or self.brand_colors
        top = p.get("background", "#1a1a2e")
        bottom = p.get("secondary_bg", top)
        img = self._gradient(top, bottom, width, height)
        if shapes:
            # translucent accent circles in the corners for depth/variety
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            d = ImageDraw.Draw(overlay)
            acc = _hex(p.get("accent", "#e94560"))
            d.ellipse([-220, -220, 260, 260], fill=acc + (40,))
            d.ellipse([width - 300, height - 300, width + 220, height + 220], fill=acc + (28,))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        return img
    
    def add_text(self, img, text, position, font_size=48, 
                 color=None, font_type="bold", max_width=30):
        """Add wrapped text to an image"""
        draw = ImageDraw.Draw(img)
        color = color or self.brand_colors["text_primary"]
        
        try:
            font = ImageFont.truetype(self.fonts[font_type], font_size)
        except OSError:
            # ponytail: size-aware default (Pillow>=10.1) so a missing TTF still
            # renders at the right scale instead of a ~10px bitmap.
            font = ImageFont.load_default(size=font_size)
        
        wrapped = textwrap.fill(text, width=max_width)
        draw.multiline_text(position, wrapped, font=font, fill=color, 
                           spacing=10)
        return img
    
    def generate_carousel_images(self, carousel_content, idea_id):
        """Generate all slides for a carousel post"""
        slides = []
        idea_dir = os.path.join(self.output_dir, f"carousel_{idea_id}")
        os.makedirs(idea_dir, exist_ok=True)
        total_pages = 2 + len(carousel_content.get("slides", []))  # hook + content + cta

        # rotate palette per post so consecutive carousels differ visually
        bt, bb, acc, txt, txt2 = PALETTES[idea_id % len(PALETTES)]
        pal = {"background": bt, "secondary_bg": bb, "accent": acc,
               "text_primary": txt, "text_secondary": txt2}
        # rotate hook layout: 0=upper, 1=centred, 2=lower — keyed off the post id
        layout = idea_id % 3
        hook_y = (300, 380, 470)[layout]

        # Slide 1: Hook slide
        img = self.create_slide(palette=pal)
        # accent bar above the hook
        ImageDraw.Draw(img).rectangle([80, hook_y - 50, 300, hook_y - 45], fill=acc)
        img = self.add_text(
            img,
            carousel_content["slide_1_hook"],
            position=(80, hook_y),
            font_size=72,
            color=txt,
        )
        if carousel_content.get("slide_1_subtext"):
            img = self.add_text(
                img,
                carousel_content["slide_1_subtext"],
                position=(80, hook_y + 220),
                font_size=36,
                color=txt2,
                font_type="regular"
            )

        img = self.add_footer(img, 1, total_pages)
        path = os.path.join(idea_dir, "slide_01.png")
        img.save(path, quality=95)
        slides.append(path)

        # Content slides
        for i, slide_data in enumerate(carousel_content.get("slides", []), 2):
            # alternate gradient direction (swap top/bottom) for slide-to-slide variety
            spal = pal if i % 2 == 0 else {**pal, "background": bb, "secondary_bg": bt}
            img = self.create_slide(palette=spal)
            
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
                color=acc
            )

            # Body
            img = self.add_text(
                img,
                slide_data["body"],
                position=(80, 380),
                font_size=36,
                color=txt2,
                font_type="regular",
                max_width=35
            )

            img = self.add_footer(img, i, total_pages)
            path = os.path.join(idea_dir, f"slide_{i:02d}.png")
            img.save(path, quality=95)
            slides.append(path)

        # CTA slide
        img = self.create_slide(palette=pal)
        img = self.add_text(
            img,
            carousel_content.get("slide_final_cta", "Follow for more"),
            position=(80, 380),
            font_size=56,
            color=acc
        )
        img = self.add_text(
            img,
            "Save this post  •  Share with a friend  •  Follow",
            position=(80, 600),
            font_size=30,
            color=txt2,
            font_type="regular"
        )
        
        img = self.add_footer(img, total_pages, total_pages)
        path = os.path.join(idea_dir, f"slide_final.png")
        img.save(path, quality=95)
        slides.append(path)
        
        return slides