# grading_utils.py

import logging
from scoring_utils import compute_step_score

logger = logging.getLogger("GradingUtils")


def normalize_latex(latex):
    if not latex:
        return ""

    latex = latex.strip()

    if latex.startswith("="):
        latex = latex[1:].strip()

    latex = latex.replace("\\times", "*")

    return latex


def prepare_steps_with_scores(steps):

    processed = []

    for s in steps:
        final_latex = normalize_latex(s.get("final_latex", ""))

        if not final_latex:
            continue

        base_score = compute_step_score(s)

        processed.append({
            "step_id": s["step_id"],

            # ✅ NEW FIELDS
            "text": s.get("text", ""),
            "original_latex": s.get("latex", ""),
            "final_latex": final_latex,

            "error_type": s.get("error_type"),
            "confidence": s.get("final_confidence"),
            "base_score": base_score
        })

    logger.info(f"Prepared {len(processed)} steps for grading")

    return processed