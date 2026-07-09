import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

if not API_KEY:
    raise Exception("GROQ_API_KEY missing")

client = Groq(api_key=API_KEY)

SYSTEM_PROMPT = """
You are Vera.

You help local businesses communicate with customers.

Always use the merchant context, trigger context,
customer context and category context.

Never invent facts.

Always return ONLY valid JSON.

Format:

{
  "subject":"",
  "body":"",
  "cta":"",
  "send_as":"vera"
}
"""


def generate(context):

    try:

        completion = client.chat.completions.create(

            model=MODEL,

            temperature=0.4,

            response_format={"type": "json_object"},

            messages=[

                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },

                {
                    "role": "user",
                    "content": context
                }

            ]

        )

        text = completion.choices[0].message.content.strip()

        return json.loads(text)

    except Exception as e:

        print("=" * 70)
        print("Groq Error")
        print(e)
        print("=" * 70)

        return None