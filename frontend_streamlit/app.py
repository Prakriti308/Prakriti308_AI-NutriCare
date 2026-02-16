import streamlit as st
import requests
import re
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Load environment variables from backend's .env ---
_env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# --- Page Config ---
st.set_page_config(
    page_title="AI-NutriCare",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://127.0.0.1:8000/api/upload/"

# --- Session State Defaults ---
_defaults = {
    "dark_mode": True,
    "diet_type": "Vegetarian",
    "age": 25,
    "bmi_value": None,
    "weight": 70.0,
    "height": 170.0,
    "chat_history": [],
    "diet_chain": None,
    "session_id": str(uuid.uuid4()),
    "generated_plan": None,
    "pending_question": None,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ============================================================
#  HELPER FUNCTIONS
# ============================================================
def extract_numeric(val_str):
    """Extract first number from a string like '180 mg/dL (High)'."""
    if not val_str or val_str == "N/A":
        return None
    m = re.search(r"(\d+\.?\d*)", str(val_str))
    return float(m.group(1)) if m else None


def classify_vital(value, vital_type):
    """Return (label, hex_color, symbol) for a vital value."""
    if value is None:
        return ("No Data", "#9CA3AF", "—")
    if vital_type == "blood_sugar":
        if value < 70:
            return ("Low", "#3B82F6", "↓")
        if value <= 85:
            return ("Slightly Low", "#06B6D4", "↘")
        if value <= 100:
            return ("Normal", "#10B981", "✓")
        if value <= 125:
            return ("Elevated", "#F59E0B", "↗")
        return ("High", "#EF4444", "↑")
    if vital_type == "cholesterol":
        if value < 150:
            return ("Normal", "#10B981", "✓")
        if value <= 199:
            return ("Borderline", "#F59E0B", "↗")
        if value <= 239:
            return ("High", "#EF4444", "↑")
        return ("Very High", "#DC2626", "⚠")
    return ("Unknown", "#9CA3AF", "?")


# ============================================================
#  DYNAMIC CSS (adapts to dark / light toggle)
# ============================================================
def build_css(dark: bool) -> str:
    # Palette
    card_bg     = "#1c1e2b" if dark else "#ffffff"
    card_border = "#2d3044" if dark else "#e5e7eb"
    txt1        = "#f0f0f5" if dark else "#1f2937"
    txt2        = "#a0a3b5" if dark else "#6b7280"
    note_bg     = "linear-gradient(135deg,#1e1b4b,#312e81)" if dark else "linear-gradient(135deg,#eef2ff,#e0e7ff)"
    note_bdr    = "#818cf8" if dark else "#6366f1"
    note_txt    = "#c7d2fe" if dark else "#312e81"
    find_bg     = "#451a03" if dark else "#fef3c7"
    find_txt    = "#fcd34d" if dark else "#92400e"
    bot_bg      = "#2d3044" if dark else "#f3f4f6"
    bot_txt     = "#e5e7eb" if dark else "#1f2937"
    app_bg      = "#0e1117" if dark else "#f8f9fb"
    sidebar_bg  = "#161821" if dark else "#ffffff"

    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;}}

/* App-level backgrounds */
.stApp{{background:{app_bg} !important;}}
[data-testid="stSidebar"]{{background:{sidebar_bg} !important;}}
[data-testid="stSidebar"] > div:first-child{{background:{sidebar_bg} !important;}}

/* --- Cards --- */
.nc-card{{
  background:{card_bg};border:1px solid {card_border};
  border-radius:16px;padding:1.25rem;margin-bottom:.75rem;
  transition:transform .15s,box-shadow .15s;
}}
.nc-card:hover{{transform:translateY(-1px);box-shadow:0 4px 14px rgba(0,0,0,.08);}}

/* Meal cards */
.meal-hdr{{font-size:1.1rem;font-weight:600;color:{txt1};margin-bottom:.7rem;padding-bottom:.45rem;border-bottom:2px solid {card_border};}}
.meal-item{{padding:5px 0;font-size:.93rem;color:{txt1};line-height:1.55;}}
.meal-cal{{margin-top:.7rem;padding-top:.45rem;border-top:1px dashed {card_border};font-weight:600;font-size:.88rem;color:#6366f1;}}

/* Doctor note */
.doc-note{{background:{note_bg};border-left:4px solid {note_bdr};padding:1.25rem;border-radius:12px;font-size:.95rem;line-height:1.7;color:{note_txt};}}

/* Vital cards */
.vital-card{{background:{card_bg};border:1px solid {card_border};border-radius:14px;padding:1rem;margin-bottom:.5rem;}}
.vital-lbl{{font-size:.82rem;color:{txt2};margin-bottom:4px;}}
.vital-val{{font-size:1.4rem;font-weight:700;margin:4px 0;}}
.vital-badge{{display:inline-block;padding:3px 12px;border-radius:20px;font-weight:600;font-size:.78rem;}}

/* Findings */
.find-tag{{display:inline-block;padding:3px 10px;border-radius:6px;font-size:.78rem;font-weight:500;margin:2px 4px 2px 0;background:{find_bg};color:{find_txt};}}

/* Source badges */
.src-badge{{display:inline-block;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:600;}}
.src-ai{{background:#dcfce7;color:#166534;}}
.src-tmpl{{background:#dbeafe;color:#1e40af;}}

/* Hero */
.hero{{text-align:center;padding:4rem 1rem 2rem;}}
.hero h1{{font-size:2.5rem;font-weight:700;color:{txt1};margin-bottom:.75rem;}}
.hero p{{font-size:1.05rem;color:{txt2};max-width:580px;margin:0 auto;line-height:1.7;}}

/* Steps */
.steps-row{{display:flex;gap:1.5rem;justify-content:center;margin:2.5rem 0;flex-wrap:wrap;}}
.step-box{{text-align:center;padding:1.5rem 1rem;border-radius:16px;background:{card_bg};border:1px solid {card_border};flex:1;min-width:200px;max-width:260px;}}
.step-num{{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;background:#6366f1;color:white;font-weight:700;font-size:.9rem;margin-bottom:.6rem;}}
.step-title{{font-weight:600;font-size:.95rem;color:{txt1};margin-bottom:.25rem;}}
.step-desc{{font-size:.82rem;color:{txt2};line-height:1.5;}}

/* Chat */
.chat-user{{display:flex;justify-content:flex-end;margin-bottom:10px;}}
.chat-user-bbl{{background:#6366f1;color:#fff;padding:10px 16px;border-radius:16px 16px 4px 16px;max-width:75%;font-size:.93rem;line-height:1.5;}}
.chat-bot{{display:flex;justify-content:flex-start;margin-bottom:10px;}}
.chat-bot-bbl{{background:{bot_bg};color:{bot_txt};padding:10px 16px;border-radius:16px 16px 16px 4px;max-width:75%;font-size:.93rem;line-height:1.5;}}

/* ---- Light-mode overrides (revert config.toml dark theme) ---- */
{"" if dark else '''
.stApp{{background:#f8f9fb !important;color:#1f2937 !important;}}
[data-testid="stSidebar"]{{background:#ffffff !important;}}
[data-testid="stSidebar"] > div:first-child{{background:#ffffff !important;}}
[data-testid="stHeader"]{{background:rgba(248,249,251,.9) !important;}}
p,span,label,li,div,.stMarkdown{{color:#1f2937 !important;}}
h1,h2,h3,h4,h5,h6{{color:#111827 !important;}}
small,.stCaption,.stCaption p{{color:#6b7280 !important;}}
[data-baseweb="select"] > div{{background:#fff !important;border-color:#e5e7eb !important;color:#1f2937 !important;}}
[data-baseweb="select"] span,[data-baseweb="select"] input{{color:#1f2937 !important;}}
[data-baseweb="input"] > div{{background:#fff !important;border-color:#e5e7eb !important;}}
[data-baseweb="input"] input{{background:#fff !important;color:#1f2937 !important;}}
.stNumberInput > div > div{{background:#fff !important;border-color:#e5e7eb !important;}}
.stNumberInput input{{color:#1f2937 !important;}}
.stNumberInput button{{background:#f3f4f6 !important;color:#1f2937 !important;border-color:#e5e7eb !important;}}
.stTextInput > div > div{{background:#fff !important;border-color:#e5e7eb !important;}}
.stTextInput input{{color:#1f2937 !important;}}
[data-testid="stFileUploader"]{{background:#fff !important;border:1px solid #e5e7eb !important;}}
[data-testid="stFileUploader"] section{{background:#fafafa !important;border:2px dashed #e5e7eb !important;}}
button[kind="secondary"]{{background:#fff !important;color:#1f2937 !important;border:1px solid #e5e7eb !important;}}
button[kind="secondary"]:hover{{background:#f3f4f6 !important;}}
.stButton > button{{color:#1f2937 !important;}}
.stExpander,.stExpander details,[data-testid="stExpander"] details{{background:#fff !important;border-color:#e5e7eb !important;}}
[data-testid="stMetric"]{{background:#fff !important;border:1px solid #e5e7eb !important;}}
[data-testid="stAlert"]{{background:#fff !important;border-color:#e5e7eb !important;}}
[data-testid="stAlert"] p{{color:#1f2937 !important;}}
hr{{border-color:#e5e7eb !important;}}
[data-testid="stChatMessage"]{{background:#f9fafb !important;border:1px solid #e5e7eb !important;}}
[data-testid="stChatMessage"] p{{color:#1f2937 !important;}}
[data-testid="stChatInput"]{{background:#fff !important;border-color:#e5e7eb !important;}}
[data-testid="stChatInput"] textarea{{background:#fff !important;color:#1f2937 !important;}}
[data-testid="stBottom"]{{background:rgba(248,249,251,.95) !important;}}
[data-baseweb="popover"],[role="listbox"]{{background:#fff !important;border-color:#e5e7eb !important;}}
[role="option"]{{background:#fff !important;color:#1f2937 !important;}}
[role="option"]:hover{{background:#f3f4f6 !important;}}
'''}

/* ---- Dark-mode extras (supplement config.toml dark theme) ---- */
{"" if not dark else '''
[data-testid="stHeader"]{{background:rgba(14,17,23,.85) !important;backdrop-filter:blur(8px);}}
[data-testid="stToolbar"]{{background:transparent !important;}}
[data-testid="stBottom"]{{background:rgba(14,17,23,.9) !important;}}
.stButton > button{{color:#E0E0E0 !important;}}
button[kind="secondary"]{{background:#2d3044 !important;color:#E0E0E0 !important;border:1px solid #3b3c52 !important;}}
button[kind="secondary"]:hover{{background:#3b3c52 !important;}}
[data-testid="stChatMessage"]{{background:#1c1e2b !important;border:1px solid #2d3044 !important;border-radius:12px !important;}}
hr{{border-color:#2d3044 !important;opacity:.5 !important;}}
::-webkit-scrollbar{{width:8px;height:8px;}}
::-webkit-scrollbar-track{{background:#0e1117;}}
::-webkit-scrollbar-thumb{{background:#2d3044;border-radius:4px;}}
::-webkit-scrollbar-thumb:hover{{background:#3b3c52;}}
'''}

#MainMenu{{visibility:hidden;}}
footer{{visibility:hidden;}}
</style>"""


# ============================================================
#  APPLY CSS
# ============================================================
is_dark = st.session_state.get("dark_mode", False)
st.markdown(build_css(is_dark), unsafe_allow_html=True)


# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🩺 AI-NutriCare")
    st.caption("Personalized Diet Plans from Medical Reports")
    st.divider()

    # File upload
    uploaded_file = st.file_uploader(
        "Upload Medical Report",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Blood test report or medical document (PDF / Image)",
    )

    # Preferences
    st.markdown("##### Preferences")
    st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian"], key="diet_type")
    st.number_input("Age", min_value=1, max_value=120, step=1, key="age")

    # BMI calculator
    with st.expander("BMI Calculator"):
        w = st.number_input("Weight (kg)", 30.0, 250.0, st.session_state.weight, 0.5)
        h = st.number_input("Height (cm)", 100.0, 250.0, st.session_state.height, 1.0)
        if st.button("Calculate", use_container_width=True):
            st.session_state.weight = w
            st.session_state.height = h
            st.session_state.bmi_value = w / ((h / 100) ** 2)
        if st.session_state.bmi_value is not None:
            bmi = st.session_state.bmi_value
            st.metric("BMI", f"{bmi:.1f}")
            if bmi < 18.5:
                st.info("Underweight")
            elif bmi < 25:
                st.success("Normal weight")
            elif bmi < 30:
                st.warning("Overweight")
            else:
                st.error("Obese")

    st.divider()

    # Generate button
    generate_btn = st.button(
        "🔬 Analyze & Generate Plan",
        type="primary",
        use_container_width=True,
        disabled=(uploaded_file is None),
    )

    st.divider()

    # Dark mode toggle — key-managed, no assignment conflict
    st.toggle("🌙 Dark Mode", key="dark_mode")
    st.caption("Powered by Groq LLaMA Vision AI")


# ============================================================
#  PROCESS UPLOAD  (runs only on button click)
# ============================================================
if generate_btn and uploaded_file:
    with st.spinner("🔬 Analyzing your report with AI — this may take a moment..."):
        try:
            files = {
                "report_file": (uploaded_file.name, uploaded_file, uploaded_file.type)
            }
            payload = {
                "diet_type": st.session_state.diet_type,
                "age": st.session_state.age,
            }
            resp = requests.post(API_URL, files=files, data=payload, timeout=120)

            if resp.status_code == 201:
                st.session_state.generated_plan = resp.json()
                st.session_state.diet_chain = None
                st.session_state.chat_history = []
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()
            else:
                st.error(f"Server error ({resp.status_code}): {resp.text[:300]}")
        except requests.exceptions.ConnectionError:
            st.error(
                "**Cannot connect to the backend.**  \n"
                "Make sure the Django server is running:  \n"
                "`cd backend && python manage.py runserver`"
            )
        except Exception as e:
            st.error(f"Something went wrong: {e}")
elif generate_btn:
    st.warning("Please upload a medical report first.")


# ============================================================
#  DISPLAY RESULTS  (persisted in session_state)
# ============================================================
if st.session_state.generated_plan:
    data = st.session_state.generated_plan
    patient = data.get("patient_info", {})
    med_data = data.get("medical_data", {})
    diet = data.get("diet_plan", {})
    plan_source = data.get("plan_source", "Unknown")

    # ---- Header ----
    hcol1, hcol2 = st.columns([4, 1])
    with hcol1:
        name = patient.get("name", "Patient")
        st.markdown("## Your Personalized Nutrition Plan")
        st.caption(
            f"Patient: **{name}** · "
            f"Age: **{patient.get('age', st.session_state.age)}** · "
            f"Diet: **{st.session_state.diet_type}**"
        )
    with hcol2:
        src_cls = "src-ai" if plan_source == "AI" else "src-tmpl"
        src_txt = "✨ AI-Generated" if plan_source == "AI" else "📋 Template"
        st.markdown(
            f'<br><span class="src-badge {src_cls}">{src_txt}</span>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ---- Meal Cards ----
    meals = [
        ("🍳", "Breakfast", "breakfast"),
        ("🍛", "Lunch", "lunch"),
        ("🥗", "Dinner", "dinner"),
    ]
    cols = st.columns(3)
    for col, (icon, title, key) in zip(cols, meals):
        with col:
            meal = diet.get(key, {})
            if isinstance(meal, str):
                st.markdown(
                    f'<div class="nc-card">'
                    f'<div class="meal-hdr">{icon} {title}</div>'
                    f'<div class="meal-item">{meal}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                items_html = "".join(
                    f'<div class="meal-item">• {it}</div>'
                    for it in meal.get("food_items", [])
                )
                cals = meal.get("total_calories", "—")
                st.markdown(
                    f'<div class="nc-card">'
                    f'<div class="meal-hdr">{icon} {title}</div>'
                    f"{items_html}"
                    f'<div class="meal-cal">⚡ {cals}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # ---- Vitals & Doctor Note ----
    vcol, ncol = st.columns([1, 2])

    with vcol:
        st.markdown("#### Key Vitals")
        vital_info = [
            ("Blood Sugar", "blood_sugar", "blood_sugar", "mg/dL"),
            ("Cholesterol", "cholesterol", "cholesterol", "mg/dL"),
        ]
        for label, key, vtype, unit in vital_info:
            raw = med_data.get(key, "N/A")
            val = extract_numeric(raw)
            status, color, sym = classify_vital(val, vtype)
            if val is not None:
                st.markdown(
                    f'<div class="vital-card">'
                    f'<div class="vital-lbl">{label}</div>'
                    f'<div class="vital-val" style="color:{color}">{int(val)} {unit}</div>'
                    f'<span class="vital-badge" style="background:{color}15;color:{color};">{sym} {status}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="vital-card">'
                    f'<div class="vital-lbl">{label}</div>'
                    f'<div style="color:#9ca3af;margin-top:4px;">Not available</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Extra vitals (simple display for hemoglobin, protein, albumin, BMI)
        extra_vitals = [
            ("Hemoglobin", "hemoglobin"),
            ("Total Protein", "total_protein"),
            ("Albumin", "albumin"),
            ("BMI", "bmi"),
        ]
        shown_extra = []
        for label, key in extra_vitals:
            val = med_data.get(key, "N/A")
            if val and str(val).strip() not in ("N/A", "", "None", "null"):
                shown_extra.append((label, val))
        if shown_extra:
            extra_html = "".join(
                f'<div style="display:flex;justify-content:space-between;padding:4px 0;">'
                f'<span style="font-size:.85rem;color:#9ca3af;">{lbl}</span>'
                f'<span style="font-size:.85rem;font-weight:600;">{v}</span></div>'
                for lbl, v in shown_extra
            )
            st.markdown(
                f'<div class="vital-card" style="margin-top:.25rem;">{extra_html}</div>',
                unsafe_allow_html=True,
            )

        findings = med_data.get("abnormal_findings", [])
        if findings:
            tags = " ".join(f'<span class="find-tag">{f}</span>' for f in findings)
            st.markdown(
                f'<div style="margin-top:.5rem;">'
                f'<b style="font-size:.85rem;">Findings</b><br>{tags}'
                f"</div>",
                unsafe_allow_html=True,
            )

    with ncol:
        st.markdown("#### Doctor's Note")
        note = diet.get("doctor_note", "No specific recommendations generated.")
        st.markdown(
            f'<div class="doc-note">👨‍⚕️ {note}</div>',
            unsafe_allow_html=True,
        )

    # ---- Chat Section ----
    st.divider()
    st.markdown("#### 💬 Chat with AI")
    st.caption(
        "Ask about your diet plan, request meal alternatives, or get nutrition advice."
    )

    # Lazy-init chatbot
    if st.session_state.diet_chain is None:
        with st.spinner("Starting AI chatbot..."):
            try:
                from rag_engine import initialize_diet_chat

                st.session_state.diet_chain = initialize_diet_chat(
                    st.session_state.generated_plan,
                    st.session_state.session_id,
                )
            except Exception as e:
                st.error(f"Could not start chatbot: {e}")

    if st.session_state.diet_chain:
        # Quick-start suggestion buttons (only show when no history)
        if not st.session_state.chat_history:
            prompts = [
                ("🍳 Breakfast info", "What should I eat for breakfast and why?"),
                ("🔄 Alternatives", "Can you suggest alternatives for my lunch?"),
                ("📊 Calories", "What are the total calories for each meal?"),
                ("❓ Why this diet?", "Why did you recommend this specific diet based on my medical data?"),
            ]
            scols = st.columns(len(prompts))
            for sc, (lbl, prm) in zip(scols, prompts):
                with sc:
                    if st.button(lbl, use_container_width=True, key=f"s_{lbl}"):
                        st.session_state.pending_question = prm
                        st.rerun()

        # Render chat history using Streamlit's native chat UI
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "👨‍⚕️"):
                st.markdown(msg["content"])

        # Handle pending question (from suggestion button click)
        if st.session_state.pending_question:
            q = st.session_state.pending_question
            st.session_state.pending_question = None
            st.session_state.chat_history.append({"role": "user", "content": q})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(q)
            with st.chat_message("assistant", avatar="👨‍⚕️"):
                with st.spinner("AI is thinking..."):
                    try:
                        ans = st.session_state.diet_chain.chat(
                            q, st.session_state.chat_history[:-1]
                        )
                    except Exception as e:
                        ans = f"Sorry, an error occurred: {e}"
                st.markdown(ans)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()

        # Free-form chat input
        user_msg = st.chat_input("Ask AI about your diet plan...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_msg)
            with st.chat_message("assistant", avatar="👨‍⚕️"):
                with st.spinner("AI is thinking..."):
                    try:
                        ans = st.session_state.diet_chain.chat(
                            user_msg, st.session_state.chat_history[:-1]
                        )
                    except Exception as e:
                        ans = f"Sorry, an error occurred: {e}"
                st.markdown(ans)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()

    elif st.session_state.diet_chain is None:
        st.info("Chatbot is initializing...")


# ============================================================
#  LANDING PAGE  (no plan generated yet)
# ============================================================
else:
    st.markdown(
        """
    <div class="hero">
        <h1>🩺 AI-NutriCare</h1>
        <p>Upload your medical report and get a personalized, AI-generated diet plan
        tailored to your health conditions, age, and dietary preferences.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="steps-row">
        <div class="step-box">
            <div class="step-num">1</div>
            <div class="step-title">Upload Report</div>
            <div class="step-desc">PDF or image of your blood test / medical report</div>
        </div>
        <div class="step-box">
            <div class="step-num">2</div>
            <div class="step-title">AI Analysis</div>
            <div class="step-desc">AI reads your vitals, detects conditions &amp; risk factors</div>
        </div>
        <div class="step-box">
            <div class="step-num">3</div>
            <div class="step-title">Get Your Plan</div>
            <div class="step-desc">Receive a meal-by-meal diet plan with calorie targets</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.info("👈 Upload a medical report in the sidebar to get started!")
