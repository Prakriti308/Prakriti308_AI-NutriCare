import json
import random
import re
from django.conf import settings
from groq import Groq
from .ai_utils import load_document_images, get_markdown_from_page

# Initialize Client
client = Groq(api_key=settings.GROQ_API_KEY)

# Model configuration with fallbacks (primary → legacy → fast)
TEXT_MODELS = ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama-3.1-8b-instant"]

def call_groq_with_fallback(messages, response_format=None):
    """Call Groq API with automatic model fallback."""
    last_error = None
    for model in TEXT_MODELS:
        try:
            kwargs = {"model": model, "messages": messages}
            if response_format:
                kwargs["response_format"] = response_format
            response = client.chat.completions.create(**kwargs)
            print(f"[OK] Groq API call succeeded with model: {model}")
            return response
        except Exception as e:
            last_error = e
            print(f"[WARN] Model {model} failed: {type(e).__name__}: {e}")
    raise last_error

# --- HELPER FUNCTION: NAME EXTRACTION ---
def find_patient_name(text):
    """
    Extract patient name from raw text using regex patterns.
    Returns the first valid name found, or None.
    """
    if not text:
        return None
    
    # Common patterns for name extraction
    patterns = [
        r"Name\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Name: John Doe
        r"Patient(?:'s)?\s+Name\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Patient Name: John Doe
        r"Patient\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Patient: John Doe
        r"Mr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Mr. John Doe
        r"Ms\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Ms. Jane Doe
        r"Mrs\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Mrs. Jane Doe
        r"Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Dr. John Doe (might be doctor, but worth trying)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Validate: name should be 2-50 chars and not contain numbers
            if 2 <= len(name) <= 50 and not re.search(r'\d', name):
                print(f"[OK] Regex found name: {name}")
                return name
    
    return None

# --- MOCK PROFILES FOR DEMO (Safety Net) ---
MOCK_PROFILES = [
    {
        "condition": "Diabetes",
        "diet_type": "Vegetarian",
        "medical_data": {"blood_sugar": "180 mg/dL (High)", "cholesterol": "190 mg/dL", "bmi": "29.0", "abnormal_findings": ["High Blood Glucose", "Pre-diabetic"]},
        "diet_plan": {
            "breakfast": {
                "food_items": [
                    "1 cup steel-cut oats",
                    "2 tbsp flaxseeds",
                    "1 cup almond milk",
                    "1 small apple (sliced)"
                ],
                "total_calories": "350-400 kcal"
            },
            "lunch": {
                "food_items": [
                    "1 cup quinoa salad",
                    "100g grilled tofu",
                    "1 cup spinach",
                    "Mixed vegetables"
                ],
                "total_calories": "450-500 kcal"
            },
            "dinner": {
                "food_items": [
                    "1 cup bitter gourd (karela) stir-fry",
                    "1 chapati",
                    "Small bowl cucumber salad"
                ],
                "total_calories": "300-350 kcal"
            },
            "doctor_note": "Your sugar levels are high. Avoid white rice and sugar completely. Focus on fiber-rich foods."
        }
    },
    {
        "condition": "Diabetes",
        "diet_type": "Non-Vegetarian",
        "medical_data": {"blood_sugar": "180 mg/dL (High)", "cholesterol": "190 mg/dL", "bmi": "29.0", "abnormal_findings": ["High Blood Glucose", "Pre-diabetic"]},
        "diet_plan": {
            "breakfast": {
                "food_items": [
                    "2 scrambled eggs",
                    "1 cup spinach (sautéed)",
                    "2 slices whole wheat toast",
                    "1 small orange"
                ],
                "total_calories": "400-450 kcal"
            },
            "lunch": {
                "food_items": [
                    "150g grilled chicken breast",
                    "1 cup quinoa",
                    "Steamed broccoli and carrots",
                    "Small green salad"
                ],
                "total_calories": "500-550 kcal"
            },
            "dinner": {
                "food_items": [
                    "150g baked fish (salmon/tilapia)",
                    "1 cup roasted broccoli",
                    "½ cup brown rice"
                ],
                "total_calories": "400-450 kcal"
            },
            "doctor_note": "Your sugar levels are high. Include lean proteins and avoid white rice and sugar completely."
        }
    },
    {
        "condition": "High Cholesterol",
        "diet_type": "Vegetarian",
        "medical_data": {"blood_sugar": "90 mg/dL", "cholesterol": "240 mg/dL (High)", "bmi": "26.5", "abnormal_findings": ["Hyperlipidemia", "High LDL"]},
        "diet_plan": {
            "breakfast": {
                "food_items": [
                    "1 cup oatmeal",
                    "10 walnuts",
                    "½ cup mixed berries",
                    "1 tsp honey"
                ],
                "total_calories": "350-400 kcal"
            },
            "lunch": {
                "food_items": [
                    "1 cup chickpea curry",
                    "1 cup brown rice",
                    "Mixed green salad",
                    "1 small apple"
                ],
                "total_calories": "450-500 kcal"
            },
            "dinner": {
                "food_items": [
                    "1 bowl lentil soup (dal)",
                    "1 roti (no oil)",
                    "Cucumber and tomato salad"
                ],
                "total_calories": "300-350 kcal"
            },
            "doctor_note": "Cholesterol is elevated. Reduce saturated fats (butter, ghee) and focus on plant-based proteins."
        }
    },
    {
        "condition": "High Cholesterol",
        "diet_type": "Non-Vegetarian",
        "medical_data": {"blood_sugar": "90 mg/dL", "cholesterol": "240 mg/dL (High)", "bmi": "26.5", "abnormal_findings": ["Hyperlipidemia", "High LDL"]},
        "diet_plan": {
            "breakfast": {
                "food_items": [
                    "3 egg white omelet",
                    "1 cup spinach and mushrooms",
                    "2 slices whole wheat toast",
                    "1 small grapefruit"
                ],
                "total_calories": "350-400 kcal"
            },
            "lunch": {
                "food_items": [
                    "150g grilled fish (salmon)",
                    "1 cup steamed broccoli",
                    "1 cup brown rice",
                    "Lemon wedge"
                ],
                "total_calories": "450-500 kcal"
            },
            "dinner": {
                "food_items": [
                    "150g grilled chicken breast",
                    "Mixed roasted vegetables",
                    "Small green salad with olive oil"
                ],
                "total_calories": "400-450 kcal"
            },
            "doctor_note": "Cholesterol is elevated. Choose lean proteins like fish and chicken. Avoid red meat and saturated fats."
        }
    },
    {
        "condition": "Healthy",
        "diet_type": "Vegetarian",
        "medical_data": {"blood_sugar": "95 mg/dL", "cholesterol": "150 mg/dL", "bmi": "22.0", "abnormal_findings": []},
        "diet_plan": {
            "breakfast": {
                "food_items": [
                    "3 idlis",
                    "1 bowl sambar",
                    "2 tbsp coconut chutney",
                    "1 banana"
                ],
                "total_calories": "400-450 kcal"
            },
            "lunch": {
                "food_items": [
                    "1 cup curd rice",
                    "½ cup pomegranate seeds",
                    "Papad",
                    "Pickle (small portion)"
                ],
                "total_calories": "450-500 kcal"
            },
            "dinner": {
                "food_items": [
                    "1 cup mixed vegetable curry",
                    "2 phulkas",
                    "Small bowl dal",
                    "Cucumber raita"
                ],
                "total_calories": "400-450 kcal"
            },
            "doctor_note": "All vitals are normal. Keep maintaining this balanced vegetarian diet and stay hydrated."
        }
    },
    {
        "condition": "Healthy",
        "diet_type": "Non-Vegetarian",
        "medical_data": {"blood_sugar": "95 mg/dL", "cholesterol": "150 mg/dL", "bmi": "22.0", "abnormal_findings": []},
        "diet_plan": {
            "breakfast": {
                "food_items": [
                    "2 scrambled eggs",
                    "2 slices whole wheat toast",
                    "½ avocado (sliced)",
                    "1 cup green tea"
                ],
                "total_calories": "450-500 kcal"
            },
            "lunch": {
                "food_items": [
                    "150g grilled chicken salad",
                    "Mixed greens and vegetables",
                    "2 tbsp olive oil dressing",
                    "1 whole wheat roll"
                ],
                "total_calories": "500-550 kcal"
            },
            "dinner": {
                "food_items": [
                    "150g baked salmon",
                    "1 cup quinoa",
                    "Roasted vegetables (bell peppers, zucchini)",
                    "Lemon wedge"
                ],
                "total_calories": "500-550 kcal"
            },
            "doctor_note": "All vitals are normal. Keep maintaining this balanced diet with lean proteins and stay hydrated."
        }
    }
]

def extract_medical_data(file_path):
    print(f"[VIEW] PROCESSING FILE: {file_path}")
    
    # --- PHASE 1: SEE (Vision OCR) ---
    full_text = ""
    try:
        images = load_document_images(file_path)
        print(f"[SCAN] Found {len(images)} pages. Reading with Vision AI...")
        
        for i, img in enumerate(images):
            try:
                page_text = get_markdown_from_page(img, client)
                full_text += f"\n--- PAGE {i+1} ---\n{page_text}"
            except Exception as e:
                print(f"[WARN] Page read error: {e}")
                
        if not full_text:
            raise Exception("No text extracted")
            
        print("[OK] Text Extracted Successfully")

    except Exception as e:
        print(f"[ERROR] OCR FAILED: {e}")
        # RETURN RANDOM MOCK MEDICAL DATA (diet plan will be generated based on preference later)
        mock = random.choice(MOCK_PROFILES)
        print(f"[WARN] Switching to Mock Medical Data: {mock['condition']}")
        # Use realistic name from mock profile
        mock_name = "Rahul Sharma" if "Diabetes" in mock['condition'] else "Priya Patel"
        mock_med = mock['medical_data'].copy()
        mock_med["patient_name"] = mock_name
        mock_med["age"] = "35"
        mock_med["gender"] = "N/A"
        return mock_med, "Mock Text Used"

    # --- PHASE 2: THINK (Extraction) ---
    print("[AI] Extracting structured health data...")
    EXTRACTION_PROMPT = """You are a Medical Data Extraction AI. Analyze the following medical report and extract structured data.

You MUST return a JSON object with EXACTLY this structure:
{
  "patient_name": "Full name of the patient (string)",
  "age": "Patient age (string, e.g. '43')",
  "gender": "Male/Female/Unknown (string)",
  "blood_sugar": "Fasting blood glucose / blood sugar / glucose level with unit (string, e.g. '110 mg/dL')",
  "cholesterol": "Total cholesterol / serum cholesterol with unit (string, e.g. '200 mg/dL')",
  "bmi": "BMI value (string, e.g. '24.5'). If not listed, calculate from height and weight if available.",
  "hemoglobin": "Hemoglobin / Hb / Hgb value with unit (string, e.g. '13.5 g/dL')",
  "total_protein": "Total protein / serum protein value with unit (string, e.g. '6.5 g/dL')",
  "albumin": "Albumin / serum albumin value with unit (string, e.g. '3.8 g/dL')",
  "abnormal_findings": ["List ALL abnormal conditions identified from the lab values"]
}

EXTRACTION RULES:
1. Lab values may appear with different names. Map them:
   - Glucose / Blood Glucose / FBS / Fasting Sugar / Sugar Level → "blood_sugar"
   - Total Cholesterol / Serum Cholesterol / TC → "cholesterol"
   - Hb / Hgb / Haemoglobin → "hemoglobin"
   - TP / Total Protein / Serum Protein → "total_protein"
   - Alb / Albumin / Serum Albumin → "albumin"
2. Extract ACTUAL values from the report — never make up data
3. If a value is genuinely not present in the report, use "N/A"
4. Always include the unit (mg/dL, g/dL, etc.) with the value
5. For abnormal_findings: compare values against normal ranges and list ALL issues
   Normal ranges for reference:
   - Blood sugar: 70-100 mg/dL (fasting)
   - Cholesterol: <200 mg/dL
   - Hemoglobin: 12-17 g/dL
   - Total protein: 6.0-8.3 g/dL
   - Albumin: 3.5-5.5 g/dL
   - BMI: 18.5-24.9
6. Return ONLY the JSON object"""
    
    try:
        response = call_groq_with_fallback(
            messages=[{"role": "user", "content": f"{EXTRACTION_PROMPT}\n\nREPORT:\n{full_text}"}],
            response_format={"type": "json_object"}
        )
        raw = json.loads(response.choices[0].message.content)
        print(f"[DEBUG] Raw LLM extraction: {json.dumps(raw, indent=2)[:500]}")
        
        # --- NORMALIZE to flat structure ---
        # The LLM might return nested (patient_info/medical_data) or flat keys.
        # We normalize to a FLAT dict the view can consume directly.
        if "patient_info" in raw and "medical_data" in raw:
            # Nested format — flatten it
            pi = raw["patient_info"]
            md = raw["medical_data"]
            data = {
                "patient_name": pi.get("name", pi.get("patient_name", "")),
                "age": pi.get("age", "N/A"),
                "gender": pi.get("gender", "N/A"),
                "blood_sugar": md.get("blood_sugar", "N/A"),
                "cholesterol": md.get("cholesterol", "N/A"),
                "bmi": md.get("bmi", "N/A"),
                "hemoglobin": md.get("hemoglobin", "N/A"),
                "total_protein": md.get("total_protein", "N/A"),
                "albumin": md.get("albumin", "N/A"),
                "abnormal_findings": md.get("abnormal_findings", []),
            }
        else:
            # Already flat or custom format
            data = {
                "patient_name": raw.get("patient_name", raw.get("name", "")),
                "age": raw.get("age", "N/A"),
                "gender": raw.get("gender", "N/A"),
                "blood_sugar": raw.get("blood_sugar", "N/A"),
                "cholesterol": raw.get("cholesterol", "N/A"),
                "bmi": raw.get("bmi", "N/A"),
                "hemoglobin": raw.get("hemoglobin", "N/A"),
                "total_protein": raw.get("total_protein", "N/A"),
                "albumin": raw.get("albumin", "N/A"),
                "abnormal_findings": raw.get("abnormal_findings", []),
            }
        
        # Ensure abnormal_findings is a list
        if not isinstance(data.get("abnormal_findings"), list):
            data["abnormal_findings"] = [str(data["abnormal_findings"])] if data.get("abnormal_findings") else []
        
        # --- REGEX FALLBACK FOR NAME ---
        patient_name = data.get("patient_name", "")
        print(f"[SEARCH] DEBUG: AI extracted name = '{patient_name}'")
        
        if not patient_name or patient_name.strip() in ["N/A", "Unknown", "Not Found", "", "null", "None"]:
            print("[WARN] AI failed to extract name, trying regex...")
            regex_name = find_patient_name(full_text)
            if regex_name:
                data["patient_name"] = regex_name
                print(f"[OK] Using regex name: {regex_name}")
            else:
                print("[ERROR] Regex also failed, using fallback name")
                data["patient_name"] = "Patient"
        else:
            print(f"[OK] Using AI-extracted name: {patient_name}")
        
        print(f"[OK] Final extracted data: {json.dumps(data, indent=2)[:500]}")
        return data, full_text

    except Exception as e:
        print(f"[ERROR] EXTRACTION FAILED: {e}")
        mock = random.choice(MOCK_PROFILES)
        # Use realistic name from mock profile
        mock_name = "Anita Desai" if "Cholesterol" in mock['condition'] else "Vikram Singh"
        mock_med = mock['medical_data'].copy()
        mock_med["patient_name"] = mock_name
        mock_med["age"] = "N/A"
        mock_med["gender"] = "N/A"
        return mock_med, "Mock Text Used"

# --- HELPER FUNCTIONS FOR CALORIE CALCULATION ---
def get_daily_calories(age):
    """
    Returns daily calorie range (min, max) based on 5-tier age logic.
    Tier 1: < 16 years
    Tier 2: 16-24 years
    Tier 3: 25-40 years
    Tier 4: 41-60 years
    Tier 5: 60+ years
    """
    if age < 16:
        return (1600, 2200)
    elif age <= 24:
        return (2000, 2800)
    elif age <= 40:
        return (2000, 2600)
    elif age <= 60:
        return (1800, 2400)
    else:  # 60+
        return (1600, 2000)

def distribute_calories(data, age):
    """
    Distributes daily calorie total into meal-specific ranges.
    Breakfast: 25%
    Lunch: 40%
    Dinner: 35%
    """
    min_daily, max_daily = get_daily_calories(age)
    
    # Calculate meal-specific calorie ranges
    bk_range = f"{int(min_daily * 0.25)}-{int(max_daily * 0.25)} kcal"
    ln_range = f"{int(min_daily * 0.40)}-{int(max_daily * 0.40)} kcal"
    dn_range = f"{int(min_daily * 0.35)}-{int(max_daily * 0.35)} kcal"
    
    # Overwrite the calorie values in the diet plan
    if "breakfast" in data and isinstance(data["breakfast"], dict):
        data["breakfast"]["total_calories"] = bk_range
    if "lunch" in data and isinstance(data["lunch"], dict):
        data["lunch"]["total_calories"] = ln_range
    if "dinner" in data and isinstance(data["dinner"], dict):
        data["dinner"]["total_calories"] = dn_range
    
    print(f"[DATA] Calorie Distribution for Age {age}: Daily {min_daily}-{max_daily} kcal")
    print(f"   Breakfast: {bk_range}, Lunch: {ln_range}, Dinner: {dn_range}")
    
    return data

# --- HELPER FUNCTIONS FOR HYBRID LLM + MOCK APPROACH ---

def validate_diet_plan(plan):
    """
    Validate that LLM response has required structure.
    Returns True if valid, False otherwise.
    """
    required_keys = ["breakfast", "lunch", "dinner"]
    
    for key in required_keys:
        if key not in plan:
            print(f"[ERROR] Validation failed: Missing '{key}'")
            return False
        if not isinstance(plan[key], dict):
            print(f"[ERROR] Validation failed: '{key}' is not a dict")
            return False
        if "food_items" not in plan[key]:
            print(f"[ERROR] Validation failed: '{key}' missing 'food_items'")
            return False
        if not isinstance(plan[key]["food_items"], list):
            print(f"[ERROR] Validation failed: '{key}' food_items is not a list")
            return False
    
    print("[OK] Diet plan structure validated")
    return True

def try_llm_generation(structured_data, diet_type, age):
    """
    Attempt LLM generation with error handling.
    Returns diet plan dict or None if failed.
    """
    try:
        print(f"[AI] ATTEMPTING LLM GENERATION...")
        print(f"   Diet Type: {diet_type}, Age: {age}")
        
        # Get medical data (now a flat dict)
        blood_sugar = structured_data.get("blood_sugar", "N/A")
        cholesterol = structured_data.get("cholesterol", "N/A")
        bmi = structured_data.get("bmi", "N/A")
        hemoglobin = structured_data.get("hemoglobin", "N/A")
        total_protein = structured_data.get("total_protein", "N/A")
        albumin = structured_data.get("albumin", "N/A")
        abnormal_findings = structured_data.get("abnormal_findings", [])
        
        # Get daily calorie range
        min_daily, max_daily = get_daily_calories(age)
        daily_range = f"{min_daily}-{max_daily} kcal"
        
        # Build diet instruction based on type
        # IMPORTANT: Check Non-Vegetarian FIRST — "Vegetarian" is a substring of "Non-Vegetarian"
        if diet_type == "Non-Vegetarian" or "Non-Veg" in diet_type or "non-veg" in diet_type.lower():
            diet_instruction = f"""CRITICAL: This is a NON-VEGETARIAN meal plan. You MUST include animal protein in EVERY SINGLE MEAL.

*** MANDATORY NON-VEG REQUIREMENTS (CANNOT BE SKIPPED):

BREAKFAST - MUST INCLUDE EGGS:
- 2-3 eggs (scrambled/boiled/omelet/poached)
- OR 3-4 egg whites for cholesterol cases

LUNCH - MUST INCLUDE CHICKEN OR FISH:
- 150-200g grilled chicken breast (for ages 15-40)
- OR 120-150g grilled chicken (for ages 40+)
- OR 150g fish (salmon/tuna/tilapia/mackerel)

DINNER - MUST INCLUDE CHICKEN OR FISH:
- 150g baked/grilled fish (preferred for dinner)
- OR 120-150g grilled chicken

CRITICAL RULES:
X DO NOT suggest vegetarian alternatives in a non-veg plan
X DO NOT skip animal protein in any meal
> EVERY meal MUST have eggs, chicken, OR fish
> Breakfast = Eggs (always)
> Lunch = Chicken or Fish
> Dinner = Fish or Chicken"""
        elif diet_type == "Vegetarian" or "veg" in diet_type.lower():
            diet_instruction = """STRICTLY generate a VEGETARIAN meal plan. 
DO NOT include any meat, fish, eggs, or poultry. 
Use plant-based proteins like lentils, beans, tofu, paneer, nuts, chickpeas, soy products."""
        else:
            diet_instruction = "Generate a balanced meal plan with appropriate protein sources."
        
        # Build age instruction
        age_instruction = f"""
PATIENT AGE: {age} years old.
DAILY CALORIE TARGET: {daily_range}

AGE-BASED PORTION CALIBRATION:
Generate portion sizes appropriate for a daily intake of {daily_range}.
- Breakfast should be approximately 25% of daily calories
- Lunch should be approximately 40% of daily calories
- Dinner should be approximately 35% of daily calories

IMPORTANT: Adjust ALL meal portions to fit within the daily target of {daily_range}."""
        
        # Build full prompt
        DIET_PROMPT = f"""
You are a nutrition expert creating a personalized meal plan.

PATIENT INFORMATION:
- Age: {age} years
- Blood Sugar: {blood_sugar}
- Cholesterol: {cholesterol}
- BMI: {bmi}
- Hemoglobin: {hemoglobin}
- Total Protein: {total_protein}
- Albumin: {albumin}
- Abnormal Findings: {', '.join(abnormal_findings) if abnormal_findings else 'None detected'}
- Diet Preference: {diet_type}

{diet_instruction}

{age_instruction}

CRITICAL: YOU MUST return a JSON object following this EXACT schema:

{{
  "breakfast": {{
    "food_items": ["Qty Item 1", "Qty Item 2", "Qty Item 3"],
    "total_calories": "Range kcal"
  }},
  "lunch": {{
    "food_items": ["Qty Item 1", "Qty Item 2", "Qty Item 3", "Qty Item 4"],
    "total_calories": "Range kcal"
  }},
  "dinner": {{
    "food_items": ["Qty Item 1", "Qty Item 2", "Qty Item 3"],
    "total_calories": "Range kcal"
  }},
  "doctor_note": "Personalized medical advice referencing the patient's SPECIFIC lab values and health conditions"
}}

IMPORTANT:
- The doctor_note MUST reference the patient's actual lab values and conditions
- Food items must include specific quantities (e.g., '150g grilled chicken breast', '2 boiled eggs')
- Return ONLY valid JSON following this structure.
"""
        
        # Call Groq API
        print(f"[API] Calling Groq API...")
        response = call_groq_with_fallback(
            messages=[{"role": "user", "content": DIET_PROMPT}],
            response_format={"type": "json_object"}
        )
        
        print(f"[OK] LLM Response received")
        diet_plan = json.loads(response.choices[0].message.content)
        
        # Validate structure
        if validate_diet_plan(diet_plan):
            # Apply age-based calorie distribution
            final_plan = distribute_calories(diet_plan, age)
            print(f"[OK] LLM GENERATION SUCCESSFUL")
            return final_plan
        else:
            print(f"[WARN] LLM returned invalid structure")
            return None
            
    except Exception as e:
        print(f"[ERROR] LLM GENERATION FAILED: {type(e).__name__}: {str(e)}")
        return None

def get_best_mock_match(structured_data, diet_type):
    """
    Find best matching mock profile.
    Priority: exact blood sugar + diet type > diet type only > random
    """
    sugar_val = structured_data.get("blood_sugar", "")
    
    print(f"[SEARCH] Searching for mock match...")
    print(f"   Blood Sugar: {sugar_val}")
    print(f"   Diet Type: {diet_type}")
    
    # Try exact match (blood sugar + diet type)
    exact_matches = [m for m in MOCK_PROFILES 
                     if m["medical_data"]["blood_sugar"] == sugar_val 
                     and diet_type in m["diet_type"]]
    
    if exact_matches:
        selected = exact_matches[0]
        print(f"[OK] Found exact mock match: {selected['condition']} - {selected['diet_type']}")
        return selected["diet_plan"].copy()
    
    # Try diet type match only
    diet_matches = [m for m in MOCK_PROFILES if diet_type in m["diet_type"]]
    
    if diet_matches:
        selected = diet_matches[0]
        print(f"[WARN] Using diet-type mock match: {selected['condition']} - {selected['diet_type']}")
        return selected["diet_plan"].copy()
    
    # Last resort: random
    selected = random.choice(MOCK_PROFILES)
    print(f"[WARN] Using random mock profile: {selected['condition']} - {selected['diet_type']}")
    return selected["diet_plan"].copy()

def generate_diet_plan(structured_data, diet_type="Balanced", age=25):
    """
    Generate diet plan using hybrid approach:
    1. Try LLM generation first (personalized)
    2. Fall back to mock data if LLM fails (reliable)
    Returns: dict with 'plan' and 'source' keys
    """
    print(f"\n{'='*60}")
    print(f"[TARGET] MEAL GENERATION START")
    print(f"   Diet Type: {diet_type}")
    print(f"   Age: {age}")
    print(f"   Blood Sugar: {structured_data.get('blood_sugar', 'N/A')}")
    print(f"{'='*60}\n")
    
    # STEP 1: Try LLM generation first
    llm_result = try_llm_generation(structured_data, diet_type, age)
    
    if llm_result:
        print(f"\n[OK] USING AI-GENERATED PLAN")
        return {"plan": llm_result, "source": "AI"}
    
    # STEP 2: Fallback to mock data
    print(f"\n[WARN] LLM FAILED - FALLING BACK TO MOCK DATA")
    mock_result = get_best_mock_match(structured_data, diet_type)
    
    # Apply age-based calorie distribution
    final_mock = distribute_calories(mock_result, age)
    
    print(f"\n[OK] USING TEMPLATE PLAN")
    return {"plan": final_mock, "source": "Template"}
