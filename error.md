# Error Classification Architecture

This document outlines how the **Multi-Agent Math Pipeline** categorizes errors during the OCR and Extraction phase (`main_pipeline.py`). Properly classifying errors is critical to ensure that a student is not unfairly penalized for an AI vision failure.

---

## 1. The Goal of Error Classification

When the AI pipeline processes a handwritten mathematical solution, discrepancies can arise from two entirely different sources:
1. **The Student Made a Mistake**: The student's logic is mathematically flawed (e.g., they wrote $2 + 2 = 5$).
2. **The AI Made a Mistake**: The student wrote $2 + 2 = 4$, but the OCR misread it as $2 + 2 = 9$ because the handwriting was messy.

If the system simply graded the final extracted text, both scenarios would result in a score of `0`, severely punishing the student for the AI's OCR failure. **Error Classification** is the mechanism used to mathematically distinguish between these two scenarios.

---

## 2. How the Classification Works

The classification logic heavily relies on the **SymPy Agent** (symbolic math logic) and the **Verifier Agent** (visual cross-referencing). 

For every step in the solution, the pipeline calculates an `error_type` and attaches it to the JSON output.

### A. Phase 1: Identifying a Discrepancy (`correction_applied`)
The pipeline first determines if a visual correction is necessary. It flags a step for correction if:
1. It contains mathematical LaTeX (`has_math = True`).
2. The Visual Verifier has low confidence in the OCR's original extraction (`verifier_conf < 0.5`).
3. The Verifier finds specific visual `issues` (e.g., "Hallucinated the number 9").
4. The Verifier proposes a `corrected_latex` string based on the raw pixels.

If these conditions are met, the pipeline overrides the original extraction with the `corrected_latex` and sets `correction_applied = True`.

### B. Phase 2: Classifying the Error (`error_type`)
If a correction was applied, the pipeline must decide *why* it was applied to inform the grader.

#### Type 1: `extraction_error`
- **Trigger**: The Visual Verifier strongly disagrees with the original OCR extraction (`verifier_conf < 0.5`).
- **Meaning**: The OCR model failed to read the image properly. The Verifier stepped in and corrected the LaTeX to match what the student *actually* wrote. 
- **Impact on Grading**: The Grader will be informed that this is an `extraction_error`. The student will receive partial or full credit because the mistake was the AI's fault, not the student's.

#### Type 2: `student_error`
- **Trigger**: If the visual extraction is deemed acceptable, but the math logic completely breaks down. The pipeline checks the `corrected_latex` against the previous step using the SymPy engine (`is_equivalent(prev_latex, corrected)`).
- **Meaning**: The OCR read the image accurately, but the mathematical statement contradicts the previous step. The student made a genuine logical leap or arithmetic error.
- **Impact on Grading**: The Grader classifies this as a `student_error`. The student is severely penalized for failing the mathematical logic.

#### Type 3: `none`
- **Trigger**: `correction_applied` is `False`.
- **Meaning**: The OCR read the text perfectly, the visual Verifier agrees (`verifier_conf >= 0.5`), and no corrections were necessary.
- **Impact on Grading**: Normal grading proceeds. The student receives full base marks (assuming the math is correct).

---

## 3. The Impact on Grading (`scoring_utils.py`)

The resulting `error_type` string is passed directly into the scoring engine, ensuring a fair `base_score` calculation before the AI LLM Grader takes over:

* **`none`**: Base score is `max_marks`.
* **`extraction_error`**: Base score is bounded by `max(0.6, final_confidence)`. This mathematically guarantees the student retains the majority of their marks, preventing the AI's poor vision from destroying their grade.
* **`student_error`**: Base score is plummeted to `max_marks * 0.2` (a flat 20% for attempting the step).

### Summary
By cross-referencing visual certainty against mathematical certainty, the error classification architecture ensures the grading pipeline is **resilient to messy handwriting** and strictly fair to the student's actual intent.
