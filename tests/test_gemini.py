
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not api_key:
    raise ValueError("Gemini API key not found in .env")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model=model,
    contents="Explain a Python syntax error in two simple sentences."
)

print("Gemini connected successfully!")
print(response.text)
