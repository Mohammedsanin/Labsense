import json
import logging
import os
from google import genai
from google.genai import types
from pydantic import BaseModel

_client = None

def get_client():
    """Lazy load Gemini client"""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set. Please configure your Gemini API key in Secrets.")
        _client = genai.Client(api_key=api_key)
    return _client

class LabResult(BaseModel):
    test_name: str
    value: str
    status: str
    explanation: str
    tip: str

def generate_summary_report(extracted_text: str, lab_results: dict, analysis: dict) -> str:
    """Generate a comprehensive summary report of the blood test analysis"""
    try:
        client = get_client()
        
        prompt = f"""You are a medical AI assistant. Create a comprehensive but concise summary report of this blood test analysis or any other reports given by the user

Extracted Text:
{extracted_text[:500]}...

Lab Results Found:
{json.dumps(lab_results, indent=2)}

Analysis Results:
{json.dumps(analysis, indent=2)}

Create a professional medical summary report that includes:
1. Patient blood test overview
2. Key findings (list abnormal values first)
3. Health status assessment
4. Recommended actions or lifestyle changes
5. When to consult a doctor

Keep it clear, concise, and in simple language. Format it as a readable report (not JSON)."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if response.text:
            return response.text
        else:
            return "Unable to generate summary report."

    except Exception as e:
        logging.error(f"Error generating summary report: {e}")
        return f"Error generating summary: {str(e)}"

def analyze_blood_report(extracted_text: str, lab_results: dict) -> dict:
    """Analyze blood test results and provide health explanations"""
    try:
        client = get_client()
        
        prompt = f"""You are a medical AI assistant. Analyze the following blood test results and provide clear, simple explanations.

Blood Test Results:
{json.dumps(lab_results, indent=2)}

For each test result, provide:
1. Status (Normal/High/Low)
2. Simple explanation of what this means
3. One practical lifestyle tip if abnormal

Respond in JSON format with this structure:
{{
  "results": [
    {{
      "test_name": "name",
      "value": "value with unit",
      "status": "Normal/High/Low",
      "explanation": "simple explanation",
      "tip": "one actionable tip"
    }}
  ],
  "overall_summary": "brief overall health summary"
}}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        if response.text:
            return json.loads(response.text)
        else:
            return {"error": "No response from AI"}

    except Exception as e:
        logging.error(f"Error analyzing blood report: {e}")
        return {"error": str(e)}

def chatbot_response(user_message: str, chat_history: list = None, report_context: str = None) -> str:
    """Generate chatbot response for health questions"""
    try:
        client = get_client()
        
        system_instruction = """You are a helpful medical AI assistant. Provide accurate, 
        empathetic health information. Always remind users to consult healthcare professionals 
        for serious concerns. Keep responses concise and easy to understand."""
        
        context = ""
        if report_context:
            context = f"\n\nUser's Blood Test Context:\n{report_context}\n"
        
        if chat_history:
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-5:]])
            context += f"\nRecent conversation:\n{history_text}\n"
        
        prompt = f"{context}\nUser question: {user_message}"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        return response.text or "I'm sorry, I couldn't generate a response."

    except Exception as e:
        logging.error(f"Chatbot error: {e}")
        return f"I encountered an error: {str(e)}"

def translate_text(text: str, target_language: str) -> str:
    """Use Gemini for translation as a fallback"""
    try:
        client = get_client()
        
        prompt = f"Translate the following text to {target_language}. Only provide the translation, no explanations:\n\n{text}"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text or text

    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text

def summarize_report(image_bytes: bytes | None = None, text: str | None = None, filename: str | None = None) -> str:
    try:
        client = get_client()

        has_text = bool(text and text.strip())
        has_image = bool(image_bytes)

        if not has_text and not has_image:
            return "No content provided to summarize. Please upload a report or provide text."

        prompt_header = "You are a helpful medical assistant. Provide a clear, layperson-friendly summary of the provided medical report content. Avoid clinical diagnosis; describe findings, possible significance, and general next steps. Include a brief safety note to consult professionals. Keep it concise."

        parts = []
        if prompt_header:
            parts.append(prompt_header)
        if has_text:
            parts.append("\nReport text:\n" + (text[:5000]))
        if has_image:
            mime = "image/jpeg" if image_bytes.startswith(b'\xff\xd8') else "image/png"
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime))
            parts.append("\nDescribe the medical report image at a high level (non-diagnostic). If text is visible, factor that in.")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction="Always include a brief non-diagnostic disclaimer."
            )
        )

        return response.text or "Unable to generate a summary."
    except Exception as e:
        logging.error(f"Report summary error: {e}")
        return f"Error generating summary: {str(e)}"

def generate_doctor_pack(extracted_text: str, lab_results: dict, analysis: dict | None = None) -> str:
    """Create a concise 'Doctor Prep Pack' for the user to take to their appointment."""
    try:
        client = get_client()
        prompt = f"""
You are a medical assistant. Build a short, clear 'Doctor Prep Pack' the patient can show a physician.
Include only useful, factual info. Avoid diagnosis.

Sections:
1) One-line reason for visit
2) Key findings (abnormal values first) — bullet list with value + simple meaning
3) 3–5 questions to ask the doctor
4) Information the doctor might request (medications, symptoms, history)
5) Safety note

Extracted text (first 600 chars):\n{extracted_text[:600]}\n\n
Parsed lab results (JSON):\n{json.dumps(lab_results, indent=2)}\n\n
AI analysis (JSON if available):\n{json.dumps(analysis or {}, indent=2)}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text or "Unable to generate doctor prep pack."
    except Exception as e:
        logging.error(f"Doctor pack error: {e}")
        return f"Error generating doctor pack: {str(e)}"

def generate_action_plan(summary_text: str | None, lab_results: dict | None = None) -> str:
    """Create a simple 7-day action plan based on the summary and/or results."""
    try:
        client = get_client()
        base_context = summary_text or ""
        prompt = f"""
You are a health coach. Create a safe, simple, non-medical 7-day action plan.
Focus on lifestyle: food, hydration, sleep, light activity, and when to seek care.
Use bullet points per day (Day 1..Day 7), 3–5 bullets each, practical and easy.
Avoid medical prescriptions. Add a short safety disclaimer at the end.

Context summary (if any):\n{base_context[:800]}\n\n
Lab results (JSON if any):\n{json.dumps(lab_results or {}, indent=2)}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text or "Unable to generate action plan."
    except Exception as e:
        logging.error(f"Action plan error: {e}")
        return f"Error generating action plan: {str(e)}"
