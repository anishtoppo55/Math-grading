# run_all.py — End-to-end: OCR pipeline → Grading pipeline

import sys
import os
import json
import logging
from dotenv import load_dotenv

# -------- RESOLVE PATHS --------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OCR_DIR = os.path.join(PROJECT_ROOT, "OCR")
GRADING_DIR = os.path.join(PROJECT_ROOT, "grading")

# Load .env from project root BEFORE any sub-module imports
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("RunAll")

# Add both directories to sys.path so their modules can be imported
sys.path.insert(0, OCR_DIR)
sys.path.insert(0, GRADING_DIR)


def run_all(image_path):
    """Run full pipeline: Image → OCR → Grading → Final Report"""

    logger.info("=" * 60)
    logger.info("FULL PIPELINE: OCR → GRADING")
    logger.info(f"Image: {image_path}")
    logger.info("=" * 60)

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # ============================================================
    # PHASE 1: OCR Pipeline
    # ============================================================
    logger.info("")
    logger.info(">>> PHASE 1: OCR Pipeline")
    logger.info("")

    # Change to OCR dir so intermediate files save there
    original_cwd = os.getcwd()
    os.chdir(OCR_DIR)

    from main_pipeline import run_pipeline as run_ocr_pipeline

    ocr_output = run_ocr_pipeline(image_path)

    # Save a copy to project root for easy access
    ocr_output_path = os.path.join(OCR_DIR, "final_output.json")
    logger.info(f"OCR output saved: {ocr_output_path}")

    os.chdir(original_cwd)

    # ============================================================
    # PHASE 2: Grading Pipeline
    # ============================================================
    logger.info("")
    logger.info(">>> PHASE 2: Grading Pipeline")
    logger.info("")

    os.chdir(GRADING_DIR)

    from grading_pipeline import run_grading_pipeline

    grading_output = run_grading_pipeline(ocr_output_path)

    os.chdir(original_cwd)

    # ============================================================
    # COMBINED REPORT
    # ============================================================
    logger.info("")
    logger.info(">>> COMBINED REPORT")
    logger.info("")

    combined = {
        "image": image_path,
        "problem": ocr_output.get("problem", ""),
        "ocr_steps": ocr_output.get("steps", []),
        "grading": grading_output
    }

    combined_path = os.path.join(PROJECT_ROOT, "combined_output.json")
    with open(combined_path, "w") as f:
        json.dump(combined, f, indent=2)

    logger.info(f"Combined output saved: {combined_path}")

    # -------- PRINT SUMMARY --------
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)

    if grading_output:
        total = grading_output.get("total_score", "?")
        max_s = grading_output.get("max_score", "?")
        logger.info(f"Score: {total}/{max_s}")
        logger.info(f"Feedback: {grading_output.get('overall_feedback', '')[:120]}")

    logger.info("")
    logger.info("Output files:")
    logger.info(f"  OCR:      {ocr_output_path}")
    logger.info(f"  Grading:  {os.path.join(GRADING_DIR, 'grading_output.json')}")
    logger.info(f"  Combined: {combined_path}")

    return combined


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_all.py <image_path>")
        print("Example: python run_all.py dataset/data/images/img_0.png")
        sys.exit(1)

    image_path = sys.argv[1]

    # Handle relative paths
    if not os.path.isabs(image_path):
        image_path = os.path.abspath(image_path)

    result = run_all(image_path)
    print("\n" + json.dumps(result.get("grading", {}), indent=2))
