import os
import logging
from io import BytesIO
from PIL import Image

def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image using Google Cloud Vision API or Gemini Vision as fallback"""
    try:
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not credentials_path:
            default_path = "credentials/google-cloud-key.json"
            if os.path.exists(default_path):
                credentials_path = default_path
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = default_path
        
        if credentials_path and os.path.exists(credentials_path):
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            
            image = vision.Image(content=image_bytes)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            if texts:
                return texts[0].description
            else:
                return "No text found in image"
        else:
            logging.info("Using Gemini Vision API for OCR (no GCP credentials found)")
            from google import genai
            from google.genai import types
            
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_api_key:
                return "Error: Neither Google Cloud credentials nor Gemini API key configured"
            
            client = genai.Client(api_key=gemini_api_key)
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg" if image_bytes.startswith(b'\xff\xd8') else "image/png",
                    ),
                    "Extract all text from this image. Return only the extracted text, no explanations or formatting.",
                ],
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "No text found in image"
            
    except Exception as e:
        logging.error(f"OCR error: {e}")
        return f"Error extracting text: {str(e)}"

def translate_text_gcp(text: str, target_language: str) -> str:
    """Translate text using Google Cloud Translation API or Gemini as fallback"""
    try:
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not credentials_path:
            default_path = "credentials/google-cloud-key.json"
            if os.path.exists(default_path):
                credentials_path = default_path
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = default_path
        
        if credentials_path and os.path.exists(credentials_path):
            from google.cloud import translate_v2 as translate
            client = translate.Client()
            
            language_codes = {
                "English": "en",
                "Hindi": "hi",
                "Spanish": "es",
                "French": "fr",
                "German": "de"
            }
            
            target_code = language_codes.get(target_language, "en")
            
            result = client.translate(text, target_language=target_code)
            
            return result['translatedText']
        else:
            logging.info("Using Gemini for translation (no GCP credentials found)")
            from gemini_helper import translate_text
            return translate_text(text, target_language)
        
    except Exception as e:
        logging.error(f"Translation error: {e}")
        from gemini_helper import translate_text
        return translate_text(text, target_language)
