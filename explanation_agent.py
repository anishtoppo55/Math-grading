# explanation_agent.py

import logging
from api_utils import call_model, parse_json_response

# -------- LOGGER SETUP --------
logger = logging.getLogger("Explainer")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def explanation_agent(problem, steps):
    """Generate explanations for high-confidence steps only."""

    logger.info("========== EXPLANATION AGENT START ==========")
    logger.info(f"Total steps received: {len(steps)}")

    # -------- FILTER STEPS --------
    filtered_steps = []

    for step in steps:
        step_id = step.get("step_id")
        final_conf = step.get("final_confidence", 0.7)

        if final_conf < 0.6:
            logger.warning(
                f"Skipping Step {step_id} due to low confidence ({final_conf})"
            )
            continue

        logger.info(
            f"Including Step {step_id} for explanation (confidence={final_conf})"
        )
        filtered_steps.append(step)

    if not filtered_steps:
        logger.warning("No high-confidence steps available for explanation")
        logger.info("========== EXPLANATION AGENT END ==========")
        return steps

    # -------- PREPARE INPUT --------
    steps_text = "\n".join(
        f"Step {s['step_id']}: {s['latex']}"
        for s in filtered_steps
    )

    logger.info(f"Preparing prompt for {len(filtered_steps)} step(s)")

    # -------- PROMPT --------
    prompt = f"""
You are a strict math explanation system.

You are given:
1. A math problem
2. A sequence of VERIFIED steps in LaTeX

Your task is to explain each step clearly and accurately.

----------------------
TASKS
----------------------

For EACH step:

1. Explain what operation is performed
2. Explain why the step is valid
3. Mention the mathematical rule or concept used

----------------------
STRICT RULES
----------------------

- DO NOT solve the problem
- DO NOT add new steps
- DO NOT assume missing steps
- Explain ONLY what is explicitly present

- DO NOT restate the LaTeX
- Focus on reasoning, not rewriting

----------------------
STYLE
----------------------

- 1–3 concise sentences
- Clear and precise language
- Prefer naming rules:
  - distributive property
  - factoring identity
  - completing square
  - etc.

----------------------
EDGE CASES
----------------------

- If step is unclear → say so briefly
- If step is incorrect → explain intent and note issue

----------------------
INPUT
----------------------

Problem:
{problem}

Steps:
{steps_text}

----------------------
OUTPUT FORMAT (STRICT JSON)
----------------------

{{
  "explanations": [
    {{
      "step_id": 1,
      "explanation": "..."
    }}
  ]
}}

----------------------
FINAL INSTRUCTION
----------------------

- Output ONLY valid JSON
- No extra text
"""

    # -------- CALL MODEL --------
    logger.info("Calling model for explanations...")
    response = call_model(contents=prompt, temperature=0.3)

    logger.info(f"Response received ({len(response.text)} chars)")
    logger.debug(f"Raw response:\n{response.text}")

    # -------- SAFE JSON PARSE --------
    try:
        result = parse_json_response(response.text)
    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.warning("Skipping explanation generation due to parsing error")
        logger.info("========== EXPLANATION AGENT END ==========")
        return steps

    explanations = result.get("explanations", [])

    logger.info(f"Parsed {len(explanations)} explanation(s)")

    # -------- LOG EACH EXPLANATION --------
    for e in explanations:
        logger.info(
            f"Step {e.get('step_id')} explanation: "
            f"{e.get('explanation', '')[:100]}"
        )

    # -------- MERGE BACK --------
    explanation_map = {
        e["step_id"]: e["explanation"]
        for e in explanations
    }

    for step in steps:
        step_id = step.get("step_id")

        if step_id in explanation_map:
            step["explanation"] = explanation_map[step_id]
        else:
            step["explanation"] = ""

    # -------- SUMMARY --------
    logger.info("========== EXPLANATION SUMMARY ==========")
    logger.info(f"Explained steps: {len(explanation_map)} / {len(steps)}")

    skipped = len(steps) - len(explanation_map)
    if skipped > 0:
        logger.warning(f"Skipped {skipped} step(s) due to low confidence")

    logger.info("========== EXPLANATION AGENT END ==========")

    return steps