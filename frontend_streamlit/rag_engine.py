"""
Dr. AI Chatbot — Direct Groq API chatbot for AI-NutriCare.
No LangChain / ChromaDB / sentence-transformers needed.
Just the Groq SDK + the user's diet plan context.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from groq import Groq

# Load env from backend/.env
_env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def format_diet_plan_to_text(data: Dict[str, Any]) -> str:
    """Convert the full API response into readable text the LLM can reference."""
    parts = []

    if "patient_info" in data:
        p = data["patient_info"]
        parts.append("PATIENT INFORMATION")
        parts.append(f"  Name: {p.get('name', 'N/A')}")
        parts.append(f"  Age: {p.get('age', 'N/A')}")
        parts.append(f"  Gender: {p.get('gender', 'N/A')}")
        parts.append("")

    if "medical_data" in data:
        m = data["medical_data"]
        parts.append("MEDICAL DATA")
        for key in ("blood_sugar", "cholesterol", "bmi", "hemoglobin",
                     "total_protein", "albumin"):
            val = m.get(key, "N/A")
            label = key.replace("_", " ").title()
            parts.append(f"  {label}: {val}")
        findings = m.get("abnormal_findings", [])
        if findings:
            parts.append(f"  Abnormal Findings: {', '.join(findings)}")
        parts.append("")

    if "diet_plan" in data:
        d = data["diet_plan"]
        parts.append("PERSONALIZED DIET PLAN")
        for meal, icon in [("breakfast", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner")]:
            if meal in d:
                parts.append(f"\n  {icon}:")
                info = d[meal]
                if isinstance(info, dict):
                    for item in info.get("food_items", []):
                        parts.append(f"    - {item}")
                    parts.append(f"    Calories: {info.get('total_calories', 'N/A')}")
                else:
                    parts.append(f"    {info}")
        if "doctor_note" in d:
            parts.append(f"\n  Doctor's Note: {d['doctor_note']}")

    if "plan_source" in data:
        parts.append(f"\n  Plan Source: {data['plan_source']}")

    return "\n".join(parts)


SYSTEM_PROMPT = """You are Dr. AI, a friendly and knowledgeable dietitian assistant for the AI-NutriCare app.

You have access to the patient's complete diet plan and medical data shown below. Use this to answer their questions accurately.

RULES:
1. Answer based on the diet plan context provided. Reference specific foods, calories, and medical values when relevant.
2. If asked for meal alternatives, suggest foods that match the same calorie range and dietary goal.
3. If the question is unrelated to diet/nutrition/health, politely redirect: "I specialize in nutrition and diet advice. How can I help with your meal plan?"
4. Be warm, encouraging, and concise. Use bullet points for lists.
5. When discussing medical values, explain what they mean in simple terms.
6. Never diagnose conditions — only provide dietary guidance.

PATIENT'S DIET PLAN & MEDICAL DATA:
{context}
"""


class DrAIChatbot:
    """Simple Groq-powered chatbot with conversation memory."""

    def __init__(self, diet_plan_data: Dict[str, Any]):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Make sure backend/.env has it set."
            )
        self.client = Groq(api_key=api_key)
        self.context = format_diet_plan_to_text(diet_plan_data)
        self.system_message = SYSTEM_PROMPT.format(context=self.context)
        # Model list with fallback
        self.models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    def chat(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """
        Send a message and get a response.

        Args:
            user_message: The user's question.
            history: List of {"role": "user"|"assistant", "content": "..."} dicts.

        Returns:
            The assistant's reply as a string.
        """
        messages = [{"role": "system", "content": self.system_message}]

        # Add conversation history (keep last 10 exchanges to stay within context)
        for msg in history[-20:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        # Add current question
        messages.append({"role": "user", "content": user_message})

        # Try models with fallback
        last_error = None
        for model in self.models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=1024,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                continue

        return f"Sorry, I'm having trouble connecting right now. Error: {last_error}"


def initialize_diet_chat(diet_plan_data: Dict[str, Any], session_id: str):
    """
    Initialize the chatbot. Returns a DrAIChatbot instance.
    Keeps same function signature so app.py doesn't need big changes.
    """
    return DrAIChatbot(diet_plan_data)
