import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL_NAME", "gemini-2.5-flash")

if not API_KEY:
    raise Exception("GEMINI_API_KEY missing in .env")

client = genai.Client(api_key=API_KEY)


SYSTEM_PROMPT = """
You are Vera.

You help merchants grow their business.

You receive complete business context.

Rules:

1. Never invent facts.

2. Use ONLY information provided.

3. Be highly personalized.

4. Mention WHY you are reaching out.

5. Use category voice.

6. One CTA only.

7. Maximum 120 words.

Return ONLY valid JSON.

Example:

{
    "subject":"...",
    "body":"...",
    "cta":"...",
    "send_as":"vera"
}
"""


def generate(context):

    response = client.models.generate_content(

        model=MODEL,

        contents=f"""

{SYSTEM_PROMPT}

{context}

"""

    )

    text = response.text.strip()

    if text.startswith("```"):

        text = text.replace("```json", "")

        text = text.replace("```", "")

        text = text.strip()

    try:

        return json.loads(text)

    except Exception:

        return {

            "subject": "Business Update",

            "body": text,

            "cta": "Reply if you'd like to know more.",

            "send_as": "vera"

        }