
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

client = genai.Client(api_key=API_KEY) if API_KEY else None


def generate_ai_response(prompt):

    if not API_KEY:
        return "AI_ERROR: Gemini API key is missing. Check your .env file."

    if not MODEL:
        return "AI_ERROR: Gemini model is not configured."

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        return response.text or "Gemini returned an empty response."

    except errors.ClientError as error:

        message = str(error).lower()

        if error.code == 429:
            return (
                "AI_QUOTA_EXCEEDED: Gemini API quota exceeded. "
                "Please try again after the quota resets."
            )

        if error.code in (401, 403):
            return (
                "AI_AUTH_ERROR: Gemini API authentication failed. "
                "Please check your API key."
            )

        if error.code == 404:
            return (
                "AI_MODEL_ERROR: The configured Gemini model "
                "was not found. Check GEMINI_MODEL in .env."
            )

        return f"AI_ERROR: Gemini API error ({error.code}): {error}"

    except errors.ServerError as error:
        return (
            "AI_SERVER_ERROR: Gemini is temporarily unavailable. "
            "Please try again later."
        )

    except Exception as error:
        print("Gemini unexpected error:", repr(error))
        return (
            "AI_ERROR: Unable to complete the Gemini request. "
            "Please check your internet connection and try again."
        )


def analyze_code(code, language, execution_result=None):

    execution_info = (
        str(execution_result)
        if execution_result is not None
        else "Code execution results not provided."
    )

    prompt = f"""
You are an expert programming code analyzer.

Analyze the following {language} code carefully.

Check for:
1. Syntax errors
2. Logical errors
3. Runtime errors
4. Code quality issues
5. Performance problems
6. Security issues

Actual execution results:
{execution_info}

For every detected issue provide:
- Error type
- Line number
- Severity
- Explanation in simple English
- Why the error occurs
- How the user can correct it

Do not modify or rewrite the original code.
Do not invent errors.
Distinguish confirmed execution errors from potential issues.
If no errors are found, clearly state that.

Code:
{code}
"""

    return generate_ai_response(prompt)


def fix_code(code, language, execution_result=None):

    prompt = f"""
You are an expert {language} programmer.

Find and fix all genuine errors in the following code.

Execution results:
{execution_result}

Requirements:
1. Correct syntax errors.
2. Correct logical errors.
3. Correct runtime errors.
4. Preserve the original program's purpose.
5. Do not unnecessarily change the code.
6. Return the complete corrected code.
7. Explain the corrections separately.

Use this format:

CORRECTED_CODE:
[Complete corrected code]

EXPLANATION:
[Explain the changes]

Original code:
{code}
"""

    return generate_ai_response(prompt)


def teach_code(code, language):

    prompt = f"""
You are a friendly programming teacher.

Teach the following {language} code to a beginner.

Explain:
1. Program purpose.
2. Important concepts used.
3. Each line or logical block step by step.
4. How the program executes.
5. Expected output.
6. Important concepts to remember.

Use simple English and examples.

Code:
{code}
"""

    return generate_ai_response(prompt)


def find_errors(code, language, execution_result=None):

    prompt = f"""
You are an expert {language} debugging assistant.

Find errors in this code.

Execution results:
{execution_result}

For every issue provide:
1. Exact line number.
2. Error type.
3. Severity.
4. Problematic code.
5. Why it is wrong.
6. How to fix it.

Distinguish confirmed errors from potential issues.
Do not invent errors.
If no errors exist, clearly say no errors were detected.

Code:
{code}
"""

    return generate_ai_response(prompt)

