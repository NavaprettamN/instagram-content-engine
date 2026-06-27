"""Generate the sellable 'AI Productivity Pack' PDF (curated prompts + templates).

Curated, hand-written prompts (a product people pay for shouldn't be generic AI
filler). Rendered with the bundled Inter fonts via fpdf2. Output lands in
generated_content/ (gitignored) so it stays PRIVATE — never commit the product
to the public repo; upload the PDF to Gumroad.

    python -m scripts.build_product
"""
import os
from fpdf import FPDF

OUT = "generated_content/ai_productivity_pack.pdf"
BG, CARD, ACCENT, TEXT, MUTED = (26, 26, 46), (22, 33, 62), (233, 69, 96), (255, 255, 255), (160, 160, 160)

PROMPTS = {
    "Writing & Communication": [
        ("Sharpen any draft", "Rewrite the text below to be 30% shorter, clearer, and more confident — keep my voice, cut hedging and filler, lead with the main point.\n\nTEXT: [paste]"),
        ("Explain it simply", "Explain [topic] to me like I'm smart but new to it. Use one analogy, 3 key points, and a 'why it matters'. Avoid jargon."),
        ("Tone shift", "Rewrite this message in a [warm / direct / formal / playful] tone without changing the facts. Give me 2 versions.\n\nMESSAGE: [paste]"),
        ("Hard message, handled", "Help me write a message that says [difficult thing] to [person/role]. Be honest but kind, keep it short, and end with a clear next step."),
        ("10 angles, instantly", "Give me 10 distinct angles to write about [topic] — surprising, contrarian, beginner, advanced, story-led, data-led. One line each."),
    ],
    "Email & Inbox": [
        ("Inbox zero reply", "Draft a concise reply to the email below. Match its tone, answer every question, and propose a clear action. Under 120 words.\n\nEMAIL: [paste]"),
        ("Follow-up that gets a response", "Write a 3-sentence follow-up to [name] about [topic]. Reference the last touchpoint, add one new reason to reply, and make the ask specific."),
        ("Decline gracefully", "Help me say no to [request] without burning the relationship. Acknowledge, decline clearly, offer one small alternative."),
    ],
    "Planning & Productivity": [
        ("Plan my week", "Here are my goals and commitments: [list]. Build a realistic weekly plan that protects 2 deep-work blocks/day, batches similar tasks, and leaves buffer. Flag anything overcommitted."),
        ("Break down a big task", "I need to [big goal] by [date]. Break it into milestones, then this-week tasks, then today's first 25-minute action. Note risks."),
        ("Decision in 5 minutes", "I'm deciding between [A] and [B]. Ask me 3 clarifying questions, then give a recommendation with the single biggest trade-off."),
        ("Beat procrastination", "I keep avoiding [task]. Ask me 2 questions to find the real blocker, then give the smallest possible first step I can do in 10 minutes."),
    ],
    "Learning & Research": [
        ("Learn anything faster", "Create a 7-day learning plan for [skill] assuming 45 min/day. Each day: one concept, one resource, one tiny practice task. End with a test of understanding."),
        ("Summarize + interrogate", "Summarize the text below in 5 bullets, then list the 3 weakest claims and what evidence would change my mind.\n\nTEXT: [paste]"),
        ("Compare options", "Compare [option A], [B], [C] for [my use case] in a table: cost, learning curve, best-for, biggest downside. Then pick one for me."),
        ("Teach back to test myself", "I just learned [topic]. Ask me 5 questions of increasing difficulty, wait for each answer, then score me and point out the one gap to fix."),
    ],
    "Content Creation": [
        ("Hook machine", "Give me 10 scroll-stopping hooks (max 8 words each) for a post about [topic]. Mix curiosity gaps, bold claims, and numbers."),
        ("Carousel from one idea", "Turn [idea] into a 7-slide carousel outline: hook slide, 5 value slides (one point each), and a save/share CTA slide."),
        ("Repurpose once, post everywhere", "Take this idea: [paste]. Give me a version for an Instagram caption, a tweet, and a LinkedIn post — same core, native to each."),
        ("Caption that converts", "Write an Instagram caption for [topic]: scroll-stopping first line, 3 short value lines, a save CTA, and a question to drive comments."),
    ],
    "Work & Career": [
        ("Meeting prep in 2 minutes", "I have a meeting about [topic] with [who]. Give me: the 1 outcome I want, 3 talking points, 2 likely objections + responses, and a strong opener."),
        ("Brag doc builder", "Turn these raw wins into 5 resume-ready bullets with metrics and action verbs: [list]."),
        ("Negotiate the ask", "Help me ask for [raise / scope / deadline change]. Draft the opener, the justification (value-focused), and a fallback position."),
    ],
    "Coding & Tech": [
        ("Debug with me", "Here's my error and code: [paste]. Don't just fix it — explain the root cause in 2 lines, give the fix, and note how to avoid it next time."),
        ("Explain this code", "Explain what this code does, line by line, then suggest the single highest-impact improvement.\n\nCODE: [paste]"),
        ("Spec before code", "I want to build [thing]. Ask me 4 questions, then write a short spec: scope, key steps, and what to skip for v1."),
    ],
    "Life Admin": [
        ("Anything, organized", "Take this brain dump and organize it into Now / Soon / Someday with a one-line next action for each Now item.\n\nDUMP: [paste]"),
        ("Compare and decide (purchases)", "I'm buying [product type] under [$budget] for [use case]. Give 3 picks with the one reason each wins and the one catch."),
        ("Script the awkward call", "Write what to say when I call [company] about [issue]. Polite, firm, with the exact outcome I'm asking for."),
        ("Meal-plan my week", "Plan [N] dinners for [diet/constraints] under [budget]. Give a grouped grocery list and note which meals reheat well."),
    ],
}


class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-14)
        self.set_font("Inter", size=8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"The AI Productivity Pack  ·  @contentengine2  ·  {self.page_no()}", align="C")


def main():
    os.makedirs("generated_content", exist_ok=True)
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.add_font("Inter", "", "fonts/Inter-Regular.ttf")
    pdf.add_font("Inter", "B", "fonts/Inter-Bold.ttf")
    pdf.set_auto_page_break(True, margin=18)

    # Cover
    pdf.add_page()
    pdf.set_fill_color(*BG)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_text_color(*TEXT)
    pdf.set_xy(20, 90)
    pdf.set_font("Inter", "B", 34)
    pdf.multi_cell(170, 14, "The AI Productivity\nPack")
    pdf.set_x(20)
    pdf.set_font("Inter", size=14)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 12, "30+ copy-paste prompts to work smarter, not harder")
    pdf.set_xy(20, 150)
    pdf.set_text_color(*ACCENT)
    pdf.set_font("Inter", "B", 12)
    pdf.cell(0, 8, "How to use: copy a prompt, replace [the brackets], paste into")
    pdf.set_xy(20, 158)
    pdf.cell(0, 8, "ChatGPT / Claude / Gemini. That's it.")

    total = sum(len(v) for v in PROMPTS.values())
    n = 0
    for category, items in PROMPTS.items():
        pdf.add_page()
        pdf.set_fill_color(*BG)
        pdf.rect(0, 0, 210, 297, "F")
        pdf.set_xy(18, 18)
        pdf.set_text_color(*ACCENT)
        pdf.set_font("Inter", "B", 18)
        pdf.cell(0, 12, category)
        pdf.ln(16)
        for title, prompt in items:
            n += 1
            pdf.set_x(18)
            pdf.set_text_color(*TEXT)
            pdf.set_font("Inter", "B", 13)
            pdf.multi_cell(174, 7, f"{n}. {title}")
            pdf.ln(1)
            pdf.set_x(18)
            pdf.set_fill_color(*CARD)
            pdf.set_text_color(220, 220, 220)
            pdf.set_font("Inter", size=11)
            pdf.multi_cell(174, 6, prompt, fill=True, padding=4)
            pdf.ln(5)

    pdf.output(OUT)
    print(f"build_product: wrote {OUT}  ({total} prompts, {pdf.page_no()} pages)")


if __name__ == "__main__":
    main()
