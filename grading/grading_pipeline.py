# grading_pipeline.py

import json
import os
import sys
import logging

from gemini_grader import gemini_grader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GradingPipeline")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def run_grading_pipeline(input_file=None):
    """
    Run grading on OCR output.
    
    Searches for final_output.json in this order:
      1. Explicit path passed as argument
      2. ../OCR/final_output.json  (from OCR pipeline)
      3. ../final_output.json      (project root fallback)
      4. ./final_output.json       (local fallback)
    """

    logger.info("===== GRADING PIPELINE START =====")

    # -------- FIND INPUT FILE --------
    if input_file and os.path.exists(input_file):
        ocr_path = input_file
    else:
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "OCR", "final_output.json"),
            os.path.join(os.path.dirname(__file__), "..", "final_output.json"),
            "final_output.json",
        ]
        ocr_path = None
        for c in candidates:
            resolved = os.path.abspath(c)
            if os.path.exists(resolved):
                ocr_path = resolved
                break

        if not ocr_path:
            logger.error("Could not find final_output.json from OCR pipeline!")
            logger.error(f"Searched: {[os.path.abspath(c) for c in candidates]}")
            return None

    logger.info(f"Loading OCR output from: {ocr_path}")

    data = load_json(ocr_path)

    problem = data.get("problem", "")
    steps = data.get("steps", [])

    logger.info(f"Problem: {problem[:80]}")
    logger.info(f"Steps to grade: {len(steps)}")

    # -------- GRADE --------
    grading = gemini_grader(problem, steps)

    if grading:
        save_json(grading, "grading_output.json")
        logger.info("Saved grading_output.json")
    else:
        logger.error("Grading returned None — model may have failed")

    logger.info("===== GRADING PIPELINE END =====")

    return grading


if __name__ == "__main__":
    # Accept optional CLI argument for input file path
    input_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_grading_pipeline(input_path)
    if result:
        print(json.dumps(result, indent=2))