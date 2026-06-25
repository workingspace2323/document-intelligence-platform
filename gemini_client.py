import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise Exception("GEMINI_API_KEY not found")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

def ask_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text