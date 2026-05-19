# gemini_grader.py

from google import genai
import os
import json
import re
import logging
from dotenv import load_dotenv 
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
from grading_utils import prepare_steps_with_scores

logger = logging.getLogger("GeminiGrader")

API_KEY = os.getenv("API_KEY")
client = genai.Client(api_key=os.getenv("API_KEY"))


def clean_json(text):
    text = re.sub(r"^```json", "", text.strip())
    text = re.sub(r"```$", "", text)
    return text


def build_prompt(problem, steps):

    return f"""
You are a strict math examiner.

Problem:
{problem}

Steps:
Each step contains:
- text → original text
- original_latex → OCR math
- final_latex → corrected math (USE THIS FOR GRADING)
- base_score → precomputed score
- error_type → error classification

Steps:
{json.dumps(steps, indent=2)}

----------------------
TASK
----------------------

1. Evaluate correctness of each step using final_latex
2. Adjust base_score slightly (±20% max)
3. Provide clear feedback

----------------------
RULES
----------------------

- error_type = "none" → normal grading
- error_type = "student_error" → keep low marks
- error_type = "extraction_error" → partial marks (DO NOT give 0)

- DO NOT drastically change base_score
- DO NOT recompute scores from scratch

----------------------
OUTPUT FORMAT (STRICT JSON)
----------------------

{{
  "total_score": 0,
  "max_score": 10,
  "step_grading": [
    {{
      "step_id": 1,
      "text": "...",
      "final_latex": "...",
      "base_score": 0,
      "final_score": 0,
      "feedback": "..."
    }}
  ],
  "overall_feedback": "..."
}}

IMPORTANT:
- Copy text and final_latex EXACTLY
- Return ONLY JSON
"""


def gemini_grader(problem, steps):

    logger.info("Gemini grading started")

    steps_input = prepare_steps_with_scores(steps)

    prompt = build_prompt(problem, steps_input)

    response = client.models.generate_content(
        model="gemma-4-31b-it",
        contents=prompt,
        config={
            "temperature": 0.2,
            "max_output_tokens": 1000
        }
    )

    text = clean_json(response.text)

    try:
        result = json.loads(text)
    except Exception:
        logger.error("Failed to parse Gemini output")
        logger.error(text)
        return None

    return result