# Scoring & Error Classification Architecture

This document explains how the **Scoring Engine** evaluates student work. Specifically, it details how the pipeline categorizes errors from the OCR phase and uses those categories to generate a mathematical `base_score` before the AI Grader (Gemini) determines the `final_score`.

---

## 1. The Core Concept

In a traditional grading AI, if the text recognized by the OCR is completely wrong, the AI assumes the student wrote the wrong answer, and the student gets a zero. 

To solve this, our multi-agent pipeline categorizes every step into an **`error_type`** (using SymPy and the visual Verifier). This `error_type` dictates the `base_score` using a deterministic mathematical formula (in `scoring_utils.py`), ensuring absolute fairness before the AI even looks at the logic.

---

## 2. Error Types and Base Score Calculation

By default, every mathematical step is worth a maximum of **2 marks** (`max_marks = 2`). The `compute_step_score()` function calculates the `base_score` for each step based strictly on its `error_type` and `final_confidence`:

### A. `none` (Perfect Step)
- **Condition**: The math checks out symbolically (SymPy), and the visual extraction was trusted (Verifier).
- **Formula**: `base_score = max_marks`
- **Result**: The student receives the full **2.00 marks**.

### B. `extraction_error` (Messy Handwriting / OCR Failure)
- **Condition**: The visual Verifier flagged that the OCR hallucinated or misread characters, but SymPy proved that the *corrected* equation makes perfect logical sense. 
- **Formula**: `base_score = max_marks * max(0.6, final_confidence)`
- **Result**: The student is **protected** from AI failure. They are guaranteed a minimum of **60%** (1.20 marks), but typically receive higher based on the fusion confidence. The AI understands the student likely wrote the correct math, even if the camera couldn't read it perfectly.

### C. `student_error` (Genuine Logical Mistake)
- **Condition**: The OCR read the image perfectly, but SymPy mathematically proved that the current step contradicts the previous step (e.g., expanding `(x+3)^2` to `x^2 + 9`).
- **Formula**: `base_score = max_marks * 0.20`
- **Result**: The student receives a flat **20%** (0.40 marks) for attempting the step, but loses the majority of the marks for failing the mathematical logic.

---

## 3. The AI Grader (Gemini)

Once the deterministic `base_score` is computed for every step, the entire array is sent to the **Gemini Grader** (`gemini_grader.py`). 

Gemini acts as the "human teacher" reviewing the rubric. It operates under strict system rules:
1. **Analyze Context**: Look at the entire problem and read the equations.
2. **Adjust Base Score**: Gemini is allowed to adjust the `base_score` by a maximum of **±20%** to generate the `final_score`.
   - *Example*: If the student made a `student_error` (base score 0.40), but it was a minor arithmetic slip rather than a fundamental misunderstanding, Gemini might bump it to 0.50 and write specific feedback.
   - *Example*: If a step is `none` (base score 2.00) but it is totally irrelevant to solving the problem, Gemini might drop it to 1.50.
3. **Generate Feedback**: Gemini writes the step-by-step natural language feedback (e.g., "Correct application of the algebraic identity") and the `overall_feedback` summary based on the trajectory of the errors.

### Summary
By forcing the AI to start from a heavily structured, mathematically proven `base_score` determined by the `error_type`, we prevent the LLM from hallucinating unfair grades, giving us a grading pipeline that is both **resilient to OCR failures** and **pedagogically sound**.
