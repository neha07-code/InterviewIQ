import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def ask_ai(messages):

    try:
        # Validate messages
        if (
            not messages
            or not isinstance(messages, list)
            or len(messages) == 0
        ):
            raise Exception("Messages array is empty.")

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise Exception(
                "OPENROUTER_API_KEY is not configured."
            )

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": messages
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            OPENROUTER_URL,
            json=payload,
            headers=headers,
            timeout=60
        )

        # Raise error for 4xx/5xx
        response.raise_for_status()

        data = response.json()

        content = (
            data
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )

        if not content or not content.strip():
            raise Exception("AI returned empty response.")

        return content

    except requests.exceptions.RequestException as error:

        print(
            "OpenRouter Error:",
            error.response.text
            if error.response is not None
            else str(error)
        )

        raise Exception("OpenRouter API Error")

    except Exception as error:

        print("OpenRouter Error:", error)

        raise Exception("OpenRouter API Error")