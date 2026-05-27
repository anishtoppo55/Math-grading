# Confidence Fusion & Gating Architecture

This document explains the mathematical and logical foundation of the **Fusion** and **Gating** mechanisms in the multi-agent pipeline, why they are essential, and how they directly influence the final student grade.

---

## 1. What is Confidence Fusion?

When the image is parsed, three distinct AI agents evaluate the same mathematical step. However, no single agent is perfectly reliable. **Confidence Fusion** is the process of combining their individual confidence scores into a single, unified `final_confidence` metric.

### Base Fusion Weights
For steps containing mathematical formulas (`has_math = True`), the base confidence is a weighted average:
- **30% Extractor Agent (`extractor_conf`)**: How confident the vision model is that it read the handwriting correctly.
- **40% SymPy Agent (`sympy_conf`)**: How confident the symbolic math engine is that the current step logically follows from the previous step.
- **30% Verifier Agent (`verifier_conf`)**: How confident the independent visual verifier is that the extracted LaTeX exactly matches the raw image pixels.

*(Note: If a step contains only English text and no math, the SymPy agent is bypassed, and the weight shifts to 60% Extractor / 40% Verifier).*

---

## 2. What is Gating?

A simple weighted average is dangerous because a critically fatal error by one agent (e.g., SymPy proving the math is completely wrong) could be masked if the other two agents report 100% confidence.

**Gating** acts as a series of hard logical thresholds (circuit breakers) that override the weighted average to prevent false positives.

### The Gating Rules (`compute_final_confidence`)
After calculating the base weighted average, the following gates are applied sequentially:

1. **Math Logic Failure Gate (`sympy_conf < 0.5`)**:
   - If SymPy detects that the step is mathematically inconsistent, the `final_confidence` is hard-capped at a maximum of `0.5`.
2. **Critical Math Contradiction (`sympy_conf < 0.3`)**:
   - If SymPy strongly rejects the mathematical equivalence, the score is further hard-capped at a maximum of `0.3`.
3. **Agent Disagreement Penalty (`abs(sympy - verifier) > 0.5`)**:
   - If SymPy says the math is perfect, but the Verifier says the text doesn't match the image at all (or vice versa), the system multiplies the `final_confidence` by `0.7` (a 30% penalty) due to the extreme conflict.
4. **Visual Mismatch Gate (`verifier_conf < 0.5 and issues`)**:
   - If the visual verifier finds specific issues (e.g., hallucinated numbers) and its confidence drops below 50%, the `final_confidence` is hard-capped at `0.4`.

---

## 3. Why is this used?

The Fusion and Gating mechanisms solve the fundamental unreliability of OCR and Large Language Models:
- **Hallucination Prevention**: Vision-language models often "guess" the next logical step instead of reading the actual messy handwriting. SymPy catches these mathematical leaps, while the Verifier catches visual discrepancies.
- **Self-Correction**: By isolating the confidence scores, the system knows exactly *when* to apply the Verifier's `corrected_latex` instead of trusting the original OCR extraction.
- **Fairness**: We must never penalize a student just because the AI failed to read their handwriting. The gating logic helps the system mathematically distinguish between an "AI reading error" and a "Student math error."

---

## 4. How Does This Affect the Grading?

The `final_confidence` score and the Fusion logic directly feed into `scoring_utils.py`, determining the exact marks the student receives.

### Error Classification
When the Fusion logic determines a correction is needed, it categorizes the error:
1. **Extraction Error (`extraction_error`)**: The Verifier has low confidence because the OCR misread a messy "5" as a "6". SymPy confirms the step is mathematically valid if we use the *corrected* LaTeX.
2. **Student Error (`student_error`)**: The visual extraction was perfect, but SymPy proves the math equation is false (e.g., $2 + 2 = 5$).

### The Scoring Algorithm (`compute_step_score`)
Based on the error classification, the student's score is calculated:

* **No Error (`none`)**: The student receives `100%` of the base marks.
* **Extraction Error (`extraction_error`)**: The student is **not** heavily penalized for the AI's bad handwriting recognition. They receive: `max_marks * max(0.6, final_confidence)`. This guarantees they retain at least 60% of the marks (often much higher) because the mistake was primarily the AI's fault.
* **Student Error (`student_error`)**: The student genuinely made a logical mistake. They are severely penalized, receiving only a flat `20%` (0.2 multiplier) of the marks for attempting the step, or `0` if the error invalidates the problem.

### Summary
Without Fusion and Gating, an OCR misread would automatically result in a `student_error`, unfairly failing the student. Gating allows the system to cross-examine itself, apply intelligent corrections, and distribute grades with human-like leniency toward bad handwriting but strictness toward bad math.
