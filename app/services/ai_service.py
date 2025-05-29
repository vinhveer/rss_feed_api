import google.generativeai as genai
from app.core.config import GEMINI_API_KEY


class GeminiService:
    @staticmethod
    def initialize():
        """Initialize Gemini API with API key"""
        genai.configure(api_key=GEMINI_API_KEY)

    @staticmethod
    def generate_text(prompt, max_tokens=1000, temperature=0.7):
        """Generate text using Gemini"""
        GeminiService.initialize()
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create a proper generation config object
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text

    @staticmethod
    def analyze_image(image_path, prompt):
        """Analyze image using Gemini Vision"""
        GeminiService.initialize()
        model = genai.GenerativeModel('gemini-pro-vision')
        image_parts = [{'mime_type': 'image/jpeg', 'file_path': image_path}]
        response = model.generate_content([prompt, *image_parts])
        return response.text

    @staticmethod
    def translate_text(text, source_lang="auto", target_lang="vi", max_tokens=2000):
        """Translate text using Gemini

        Args:
            text (str): Text to translate
            source_lang (str): Source language code or "auto" for auto-detection
            target_lang (str): Target language code
            max_tokens (int): Maximum tokens for response

        Returns:
            str: Translated text
        """
        GeminiService.initialize()
        model = genai.GenerativeModel('gemini-2.0-flash')

        if source_lang == "auto":
            prompt = f"""Translate the following text to {target_lang}:

            {text}
            
            Return only the translated text without any explanations or additional text.
            """
        else:
            prompt = f"""Translate the following text from {source_lang} to {target_lang}:

            {text}
            
            Return only the translated text without any explanations or additional text.
            """

        # Create a proper generation config object
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.2  # Lower temperature for more accurate translation
        )

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        return response.text