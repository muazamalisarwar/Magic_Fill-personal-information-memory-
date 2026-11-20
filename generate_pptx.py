import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette
    BG_DARK = RGBColor(11, 13, 12)       # #0B0D0C
    CARD_DARK = RGBColor(20, 23, 21)     # #141715
    CARD_INNER = RGBColor(25, 29, 26)    # #191D1A
    BORDER_DARK = RGBColor(43, 49, 44)   # #2B312C
    LIME = RGBColor(183, 243, 74)        # #B7F34A
    WHITE = RGBColor(255, 255, 255)      # #FFFFFF
    TEXT_MUTED = RGBColor(161, 170, 161) # #A1AAA1
    TEXT_DIM = RGBColor(94, 102, 94)     # #5E665E
    ROSE = RGBColor(251, 113, 133)       # #FB7185
    AMBER = RGBColor(251, 191, 36)       # #FBBF24

    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return bg

    def add_header(slide, badge_text, title_text, subtitle_text=None):
        # Badge
        badge_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf = badge_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = badge_text.upper()
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = LIME
        p.font.name = "Arial"

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.9))
        tf2 = title_box.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = title_text
        p2.font.size = Pt(22)
        p2.font.bold = True
        p2.font.color.rgb = WHITE
        p2.font.name = "Arial"

        if subtitle_text:
            p3 = tf2.add_paragraph()
            p3.text = subtitle_text
            p3.font.size = Pt(12)
            p3.font.color.rgb = TEXT_MUTED
            p3.font.name = "Arial"

    def add_card(slide, left, top, width, height, fill_color=CARD_INNER, border_color=BORDER_DARK):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # ==========================================
    # SLIDE 1: THE HOOK
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    add_header(s1, "01 / The Real-World Reality", "THE RECRUITMENT FRICTION CRISIS")

    # Big 71% Number
    num_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.8), Inches(2.2))
    tf = num_box.text_frame
    p = tf.paragraphs[0]
    p.text = "71%"
    p.font.size = Pt(110)
    p.font.bold = True
    p.font.color.rgb = LIME
    p.font.name = "Arial"

    # Headline
    head_box = s1.shapes.add_textbox(Inches(0.8), Inches(4.0), Inches(6.0), Inches(2.2))
    tf = head_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "OF CANDIDATES HAVE ABANDONED A JOB APPLICATION BECAUSE IT WAS TOO LONG OR COMPLICATED."
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = "Arial"

    # Supporting Card 1 (60%)
    add_card(s1, Inches(7.2), Inches(1.8), Inches(5.3), Inches(1.8))
    c1_box = s1.shapes.add_textbox(Inches(7.4), Inches(1.9), Inches(4.9), Inches(1.5))
    tf = c1_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "60%"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = LIME
    p.font.name = "Arial"
    p2 = tf.add_paragraph()
    p2.text = "of IT and technology candidates actively complain about repeating information already available on their CV."
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_MUTED
    p2.font.name = "Arial"

    # Supporting Card 2 (45%)
    add_card(s1, Inches(7.2), Inches(3.8), Inches(5.3), Inches(1.8))
    c2_box = s1.shapes.add_textbox(Inches(7.4), Inches(3.9), Inches(4.9), Inches(1.5))
    tf = c2_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "45%"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = "Arial"
    p2 = tf.add_paragraph()
    p2.text = "of candidates report chronic frustration with re-typing work history and education across multiple job websites."
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_MUTED
    p2.font.name = "Arial"

    # Source Footer
    src_box = s1.shapes.add_textbox(Inches(0.8), Inches(6.6), Inches(11.7), Inches(0.4))
    tf = src_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Source: CV-Library Candidate Behaviour Barometer 2026 (The Recruitment Trust Gap)"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_DIM
    p.font.name = "Arial"

    # ==========================================
    # SLIDE 2: THE PROBLEM
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "02 / The Core Problem", "WHY ARE WE STILL FILLING OUT THE SAME INFORMATION AGAIN AND AGAIN?")

    # Visual Journey Bar
    add_card(s2, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.1), fill_color=CARD_DARK)
    j_box = s2.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(11.3), Inches(0.9))
    tf = j_box.text_frame
    p = tf.paragraphs[0]
    p.text = "THE REPETITIVE LOOP:  Your CV  ➔  Job Portal 1 (35 fields)  ➔  Job Portal 2  ➔  Job Portal 3  ➔  Job Portal 4..."
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = LIME
    p.font.name = "Arial"

    # Left: What is repeatedly filled
    add_card(s2, Inches(0.8), Inches(3.1), Inches(5.7), Inches(3.2))
    l_box = s2.shapes.add_textbox(Inches(1.0), Inches(3.25), Inches(5.3), Inches(2.9))
    tf = l_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Information Repeated on Every Application:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = WHITE
    items = [
        "• Full Name, Email, Mobile Phone & Address",
        "• Education, Degrees, GPA & Graduation Dates",
        "• Work Experience, Past Job Titles & Responsibilities",
        "• Technical Skills, Frameworks & Languages",
        "• Portfolio Links, GitHub, LinkedIn & Certifications"
    ]
    for it in items:
        p_it = tf.add_paragraph()
        p_it.text = it
        p_it.font.size = Pt(11)
        p_it.font.color.rgb = TEXT_MUTED

    # Right: Consequences
    add_card(s2, Inches(6.8), Inches(3.1), Inches(5.7), Inches(3.2))
    r_box = s2.shapes.add_textbox(Inches(7.0), Inches(3.25), Inches(5.3), Inches(2.9))
    tf = r_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The Human & Career Consequences:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = ROSE
    consequences = [
        "• Wasted Time: Hours burned copying text between windows.",
        "• Repetitive Manual Work: Mindless copy-paste fatigue.",
        "• Typing Mistakes: Fatigue causes errors in dates & contact info.",
        "• Inconsistent Information: Discrepancies across various portals.",
        "• Reduced Motivation: Great candidates give up on lengthy forms."
    ]
    for c in consequences:
        p_c = tf.add_paragraph()
        p_c.text = c
        p_c.font.size = Pt(11)
        p_c.font.color.rgb = TEXT_MUTED

    # Footer note
    f_box = s2.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.4))
    tf = f_box.text_frame
    p = tf.paragraphs[0]
    p.text = "The friction does not exist because candidates lack qualifications — it exists because tools lack memory."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DIM

    # ==========================================
    # SLIDE 3: WHY EXISTING SOLUTIONS ARE NOT ENOUGH
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "03 / The Market Gap", "AUTOFILL EXISTS. BUT DOES IT REALLY UNDERSTAND YOU?", "Traditional browser autofill is built for ecommerce checkout, not professional career profiles.")

    # Left: Traditional Autofill
    add_card(s3, Inches(0.8), Inches(2.0), Inches(5.7), Inches(4.3))
    t_box = s3.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(5.3), Inches(4.0))
    tf = t_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Traditional Browser Autofill (Brittle & Rigid)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ROSE
    t_items = [
        "✕ Mainly depends on saved browser form history.",
        "✕ Relies strictly on exact, recognizable field names.",
        "✕ Completely breaks on custom ATS job portal questions.",
        "✕ Does not understand your complete professional profile.",
        "✕ Zero semantic inference: cannot map 'Contact No.' to 'Phone'."
    ]
    for it in t_items:
        p_it = tf.add_paragraph()
        p_it.text = it
        p_it.font.size = Pt(12)
        p_it.font.color.rgb = TEXT_MUTED

    # Right: Magic Fill Context-Aware Memory
    add_card(s3, Inches(6.8), Inches(2.0), Inches(5.7), Inches(4.3), border_color=LIME)
    m_box = s3.shapes.add_textbox(Inches(7.0), Inches(2.15), Inches(5.3), Inches(4.0))
    tf = m_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Magic Fill Context-Aware Memory (Intelligent)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = LIME
    m_items = [
        "✓ Unified personal memory vault of verified career history.",
        "✓ Evaluates field labels, placeholders & surrounding DOM context.",
        "✓ Seamlessly handles complex ATS forms (Workday, Greenhouse, etc.).",
        "✓ Distinguishes full-time roles, internships, degrees & skills.",
        "✓ Deterministic mapping: 100% precision with zero hallucination."
    ]
    for it in m_items:
        p_it = tf.add_paragraph()
        p_it.text = it
        p_it.font.size = Pt(12)
        p_it.font.color.rgb = WHITE

    # Footer note
    f_box = s3.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.4))
    tf = f_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Browser autofill remembers keystrokes. Magic Fill understands who you are."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DIM

    # ==========================================
    # SLIDE 4: INTRODUCING OUR SOLUTION
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "04 / The Innovation", "MEET MAGIC FILL — YOUR PERSONAL AI APPLICATION ASSISTANT.")

    # Definition Box
    def_card = add_card(s4, Inches(0.8), Inches(1.9), Inches(11.7), Inches(1.0), fill_color=CARD_DARK, border_color=LIME)
    d_box = s4.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(11.3), Inches(0.9))
    tf = d_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = '"Magic Fill is an AI-powered browser extension that intelligently stores, understands, retrieves, and automatically fills users\' personal and professional information into online forms."'
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = LIME

    # Left: Central Idea
    add_card(s4, Inches(0.8), Inches(3.1), Inches(5.7), Inches(3.2))
    ci_box = s4.shapes.add_textbox(Inches(1.0), Inches(3.25), Inches(5.3), Inches(2.9))
    tf = ci_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The Central Idea: Reusable Personal Memory"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p2 = tf.add_paragraph()
    p2.text = "Instead of repeatedly typing into every application, users create a reusable personal information memory. Magic Fill reads what the form is asking and retrieves the exact verified answer."
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_MUTED

    p3 = tf.add_paragraph()
    p3.text = "\nCORE MANTRA:"
    p3.font.size = Pt(11)
    p3.font.bold = True
    p3.font.color.rgb = LIME
    p4 = tf.add_paragraph()
    p4.text = "Enter your information once.\nReuse it intelligently whenever you need it."
    p4.font.size = Pt(14)
    p4.font.bold = True
    p4.font.color.rgb = WHITE

    # Right: Browser Autofill Mockup
    add_card(s4, Inches(6.8), Inches(3.1), Inches(5.7), Inches(3.2), fill_color=CARD_DARK)
    mo_box = s4.shapes.add_textbox(Inches(7.0), Inches(3.25), Inches(5.3), Inches(2.9))
    tf = mo_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⚡ Magic Fill Live Form Interaction"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = LIME
    mock_fields = [
        "• Full Name ➔ 'Ch Muazam Ali' (100% Match)",
        "• Highest Degree ➔ 'BS Software Engineering'",
        "• Current Title ➔ 'Lead AI Engineer'",
        "• Technical Skills ➔ 'Python, FastAPI, TypeScript, React'",
        "• Status: 7 fields matched in 0.12 seconds"
    ]
    for mf in mock_fields:
        p_mf = tf.add_paragraph()
        p_mf.text = mf
        p_mf.font.size = Pt(11)
        p_mf.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 5: HOW MAGIC FILL WORKS
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "05 / System Architecture", "FROM PERSONAL INFORMATION TO INTELLIGENT FORM COMPLETION.")

    # Flow Banner
    add_card(s5, Inches(0.8), Inches(1.8), Inches(11.7), Inches(0.8), fill_color=CARD_DARK)
    fb_box = s5.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(11.3), Inches(0.6))
    tf = fb_box.text_frame
    p = tf.paragraphs[0]
    p.text = "USER INFO  ➔  PERSONAL MEMORY  ➔  FIELD UNDERSTANDING  ➔  SEMANTIC MATCHING  ➔  AUTO FILLING"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = LIME

    # 5 Step Cards
    step_w = Inches(2.2)
    gap = Inches(0.18)
    steps = [
        ("STEP 01", "Create Memory", "Add career & personal info via dashboard, AI chatbot, or PDF CV extraction."),
        ("STEP 02", "Organize & Store", "Backend parses and stores structured records into verified memory tables."),
        ("STEP 03", "Understand Form", "Browser extension inspects input elements, labels, and form structure."),
        ("STEP 04", "Semantic Match", "AI matches field semantics with stored personal attributes deterministically."),
        ("STEP 05", "Fill The Form", "Extension automatically injects values into fields with verified 0.12s speed.")
    ]
    for i, (tag, title, desc) in enumerate(steps):
        s_left = Inches(0.8) + i * (step_w + gap)
        border = LIME if i == 4 else BORDER_DARK
        add_card(s5, s_left, Inches(2.8), step_w, Inches(3.4), border_color=border)
        s_box = s5.shapes.add_textbox(s_left + Inches(0.15), Inches(2.95), step_w - Inches(0.3), Inches(3.1))
        tf = s_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = LIME
        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(13)
        p2.font.bold = True
        p2.font.color.rgb = WHITE
        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.size = Pt(10)
        p3.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 6: WHAT MAKES MAGIC FILL DIFFERENT
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "06 / Competitive Advantage", "NOT JUST AUTOFILL. IT'S YOUR PERSONAL INFORMATION MEMORY.")

    features = [
        ("🧠 1. Intelligent Memory", "Maintains reusable personal, academic, and professional information."),
        ("🔍 2. AI Understanding", "Uses contextual semantic matching instead of relying only on field names."),
        ("📥 3. Multiple Sources", "Builds memory via documents, PDF CVs, and conversational chatbot entry."),
        ("🧩 4. Browser Integration", "Brings intelligent completion directly into the user's browsing experience."),
        ("🛡️ 5. User-Controlled", "Users can view, manage, edit, and update stored records anytime."),
        ("⚙️ 6. Extensible AI", "Configurable LLM architecture: users can provide their own AI API keys.")
    ]
    cw = Inches(3.7)
    ch = Inches(1.9)
    for idx, (title, desc) in enumerate(features):
        r = idx // 3
        c = idx % 3
        c_left = Inches(0.8) + c * (cw + Inches(0.3))
        c_top = Inches(2.0) + r * (ch + Inches(0.3))
        add_card(s6, c_left, c_top, cw, ch)
        f_box = s6.shapes.add_textbox(c_left + Inches(0.15), c_top + Inches(0.15), cw - Inches(0.3), ch - Inches(0.3))
        tf = f_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_MUTED

    f_box = s6.shapes.add_textbox(Inches(0.8), Inches(6.6), Inches(11.7), Inches(0.4))
    tf = f_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Implemented & Verified in Current Project Repository • Zero Placeholders"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_DIM

    # ==========================================
    # SLIDE 7: A REAL-WORLD EXAMPLE
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "07 / Scenario Contrast", "IMAGINE APPLYING TO 10 DIFFERENT JOBS.")

    # Left: Without Magic Fill
    add_card(s7, Inches(0.8), Inches(1.9), Inches(5.7), Inches(4.3), border_color=ROSE)
    wo_box = s7.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(5.3), Inches(4.0))
    tf = wo_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "WITHOUT MAGIC FILL (Manual Repetition)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ROSE
    wo_steps = [
        "1. Open a job application portal in a new tab.",
        "2. Read every single field label carefully.",
        "3. Open CV PDF to find the exact details.",
        "4. Copy and paste into 20–40 individual fields.",
        "5. Repeat the entire painful process for 10 websites.",
        "\nResult: Severe application fatigue, typos, and high drop-off."
    ]
    for wos in wo_steps:
        p_wos = tf.add_paragraph()
        p_wos.text = wos
        p_wos.font.size = Pt(12)
        p_wos.font.color.rgb = TEXT_MUTED

    # Right: With Magic Fill
    add_card(s7, Inches(6.8), Inches(1.9), Inches(5.7), Inches(4.3), border_color=LIME)
    w_box = s7.shapes.add_textbox(Inches(7.0), Inches(2.05), Inches(5.3), Inches(4.0))
    tf = w_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "WITH MAGIC FILL (Intelligent Automation)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = LIME
    w_steps = [
        "1. Open any job application form in your browser.",
        "2. Let Magic Fill automatically identify the input fields.",
        "3. Retrieves verified answers from personal memory.",
        "4. Fills supported fields intelligently in 1 click.",
        "5. Review the completed form and click Submit.",
        "\nResult: 0 copy-pasting, consistent accuracy, and zero burnout."
    ]
    for ws in w_steps:
        p_ws = tf.add_paragraph()
        p_ws.text = ws
        p_ws.font.size = Pt(12)
        p_ws.font.color.rgb = WHITE

    # ==========================================
    # SLIDE 8: BENEFITS AND REAL-WORLD IMPACT
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "08 / Impact & Value", "LESS REPETITION. MORE OPPORTUNITIES.")

    b_items = [
        ("⚡ Saves Manual Effort", "Eliminates repetitive re-entry across dozens of company career pages."),
        ("🎯 Prevents Typing Errors", "Ensures contact info, GPA, and job titles remain accurate and consistent."),
        ("🗄️ Centralized Memory", "Creates a single reusable personal vault that serves your entire career."),
        ("🚀 Higher Application Volume", "Removes friction, enabling candidates to apply to more opportunities.")
    ]
    bw = Inches(2.75)
    bgap = Inches(0.2)
    for i, (b_title, b_desc) in enumerate(b_items):
        b_left = Inches(0.8) + i * (bw + bgap)
        add_card(s8, b_left, Inches(1.9), bw, Inches(2.3))
        b_box = s8.shapes.add_textbox(b_left + Inches(0.15), Inches(2.05), bw - Inches(0.3), Inches(2.0))
        tf = b_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = b_title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p2 = tf.add_paragraph()
        p2.text = b_desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_MUTED

    # Big Concluding Banner
    add_card(s8, Inches(0.8), Inches(4.6), Inches(11.7), Inches(1.6), fill_color=CARD_DARK, border_color=LIME)
    c_box = s8.shapes.add_textbox(Inches(1.0), Inches(4.85), Inches(11.3), Inches(1.2))
    tf = c_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = '"Your time should be spent finding opportunities,\nnot repeatedly typing your own information."'
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # ==========================================
    # SLIDE 9: THE BIGGER VISION
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "09 / The Future Vision", "WE ARE REIMAGINING HOW PEOPLE INTERACT WITH INFORMATION.")

    # Left: Implemented Today
    add_card(s9, Inches(0.8), Inches(1.9), Inches(5.7), Inches(3.0), border_color=LIME)
    it_box = s9.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(5.3), Inches(2.7))
    tf = it_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Implemented Scope Today"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = LIME
    today_items = [
        "✓ Online Job Application Portals",
        "✓ Internship & Co-op Applications",
        "✓ AI CV / Resume Document Extraction",
        "✓ Verified Personal Memory Vault & Extension"
    ]
    for ti in today_items:
        p_ti = tf.add_paragraph()
        p_ti.text = ti
        p_ti.font.size = Pt(12)
        p_ti.font.color.rgb = WHITE

    # Right: Future Possibilities
    add_card(s9, Inches(6.8), Inches(1.9), Inches(5.7), Inches(3.0))
    fut_box = s9.shapes.add_textbox(Inches(7.0), Inches(2.05), Inches(5.3), Inches(2.7))
    tf = fut_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Expanded Future Possibilities"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE
    future_items = [
        "➔ University Admission Applications",
        "➔ Scholarship & Grant Registration",
        "➔ Complex Government & Civil Services Forms",
        "➔ Universal Digital Identity Automation"
    ]
    for fi in future_items:
        p_fi = tf.add_paragraph()
        p_fi.text = fi
        p_fi.font.size = Pt(12)
        p_fi.font.color.rgb = TEXT_MUTED

    # Mantra Box
    add_card(s9, Inches(0.8), Inches(5.2), Inches(11.7), Inches(1.2), fill_color=CARD_DARK)
    m_box = s9.shapes.add_textbox(Inches(1.0), Inches(5.35), Inches(11.3), Inches(0.9))
    tf = m_box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "ONE PERSONAL MEMORY. MULTIPLE APPLICATIONS. LESS REPETITIVE WORK."
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = LIME

    # ==========================================
    # SLIDE 10: TRANSITION TO DEMO (EXACT MANDATED TITLE)
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)

    # Big ⚡ Icon
    ico_card = add_card(s10, Inches(5.9), Inches(1.3), Inches(1.5), Inches(1.5), fill_color=LIME, border_color=LIME)
    i_box = s10.shapes.add_textbox(Inches(5.9), Inches(1.3), Inches(1.5), Inches(1.5))
    tf = i_box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "⚡"
    p.font.size = Pt(64)

    # EXACT MANDATED TITLE
    demo_box = s10.shapes.add_textbox(Inches(1.0), Inches(3.2), Inches(11.3), Inches(1.5))
    tf = demo_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "NOW WE ARE GOING TO START THE DEMO"
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = "Arial"

    # Supporting line
    sup_box = s10.shapes.add_textbox(Inches(1.5), Inches(4.7), Inches(10.3), Inches(1.0))
    tf = sup_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Let's see how Magic Fill turns repetitive form filling into an intelligent, effortless experience."
    p.font.size = Pt(18)
    p.font.color.rgb = TEXT_MUTED
    p.font.name = "Arial"

    # Status pills
    f_box = s10.shapes.add_textbox(Inches(1.0), Inches(6.0), Inches(11.3), Inches(0.5))
    tf = f_box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Live Form Simulator • Chrome Extension v1.2 MV3 • Real-Time Personal Memory"
    p.font.size = Pt(12)
    p.font.color.rgb = LIME

    # Save presentation
    output_path = "presentation.pptx"
    prs.save(output_path)
    print(f"Presentation generated successfully at: {output_path}")

if __name__ == "__main__":
    create_deck()
