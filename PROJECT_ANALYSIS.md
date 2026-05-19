# Multi-Agent Math OCR & Grading System - Project Analysis

## Project Overview

This is an intelligent **end-to-end handwritten math solution processing system** that:
1. **Extracts** mathematical expressions from handwritten problem images using multi-agent OCR
2. **Validates** mathematical correctness using symbolic computation
3. **Verifies** extracted content against the original image
4. **Grades** solutions automatically using AI-powered evaluation

The system combines **computer vision, large language models (LLMs), symbolic mathematics, and intelligent grading** to create a comprehensive math assessment pipeline.

---

## Architecture Overview

```
Input Image
    ↓
[OCR PIPELINE] (Phase 1)
    ├─ Preprocessing Agent (image cleaning/enhancement)
    ├─ Extraction Agent (LLM-based math/text extraction)
    ├─ SymPy Agent (symbolic validation)
    ├─ Verifier Agent (vision-based verification)
    └─ Output: final_output.json
    ↓
[GRADING PIPELINE] (Phase 2)
    ├─ Load extracted steps
    ├─ Compute base scores (confidence + error classification)
    └─ Gemini Grader (AI-powered evaluation + feedback)
    ↓
[COMBINED REPORT]
    └─ merged results + grading feedback
```

---

## Detailed Component Breakdown

### **PHASE 1: OCR PIPELINE** (OCR/main_pipeline.py)

The OCR pipeline processes an image through 4 sequential agents to extract and validate mathematical content.

#### 1. **Preprocessing Agent** (OCR/preprocessing_agent.py)
**Purpose:** Enhance image quality for better OCR results

**Process:**
- **Image Loading:** Read image using OpenCV
- **Early Resizing:** Scale image to max 1024px (matches API limits) for efficiency
- **Grayscale Conversion:** Convert to grayscale for processing
- **Denoising:** Apply NLMeansDenoising to remove noise
- **Contrast Enhancement:** Use CLAHE (Contrast Limited Adaptive Histogram Equalization)
- **Adaptive Thresholding:** Apply Gaussian adaptive threshold to create binary image
- **Content Cropping:** Detect and crop to actual content (remove empty margins with 20px padding)
- **Output:** Saved as JPEG (quality 90) for upload efficiency

**Key Settings:**
- Target max dimension: 1024px
- Denoising: 30 strength, 7 filter strength, 21 template size
- CLAHE: clipLimit=2.0, tileGridSize=(8,8)
- Threshold: blockSize=11, constant=2

---

#### 2. **Extraction Agent** (OCR/extractor_agent.py)
**Purpose:** Extract problem statement and solution steps with both text and mathematical LaTeX

**Process:**
- **Model Used:** Gemma 4 (31B-IT variant) via Google GenAI
- **Input:** Preprocessed image + detailed instruction prompt
- **Temperature:** 0.1 (deterministic, focused extraction)
- **Output Format:** JSON with strict structure

**Output Structure:**
```json
{
  "problem": "...",  // Problem statement
  "steps": [
    {
      "step_id": 1,
      "text": "...",      // Full OCR text (includes words + math)
      "latex": "...",     // Math-only LaTeX (NO words, NO $ symbols)
      "confidence": 0.85  // Extractor's confidence [0-1]
    }
  ]
}
```

**Key Rules Enforced:**
- `text`: Full content exactly as seen (words + math expressions)
- `latex`: ONLY mathematical expressions, stripped of text
- Non-math content → `latex = ""`
- Unclear math → `latex = "[unclear]"`
- Returns ONLY JSON (strict parsing)

---

#### 3. **SymPy Agent** (OCR/sympy_agent.py)
**Purpose:** Validate mathematical syntax and detect parsing errors

**Process:**
- **LaTeX Cleaning:**
  - Remove $ delimiters
  - Remove common filler words (Observe, Therefore, Hence, Thus, So)
  - Remove explanatory text in parentheses
  - Strip stray text before equations

- **Validation Logic:**
  - Empty check → confidence = 0.0
  - Matrix detection → confidence = 0.7 (skip SymPy parsing, matrices not supported)
  - Equation handling → parse both sides separately
  - Expression parsing → attempt SymPy parse_latex
  
- **Error Handling:**
  - Division by zero detection
  - Domain violations (sqrt of negative, log of zero)
  - Syntax errors with recovery suggestions

**Confidence Scoring:**
- 1.0 = Fully valid, error-free
- 0.8 = Valid but minor issues
- 0.6 = Marginal (warnings present)
- 0.0 = Invalid syntax

---

#### 4. **Verifier Agent** (OCR/verifier_agent.py)
**Purpose:** Cross-check extracted text/LaTeX against the original image using vision

**Process:**
- **Model Used:** Gemma 4 (31B-IT variant)
- **Inputs:** 
  - Original preprocessed image
  - Extracted steps (text, LaTeX)
- **Temperature:** 0.1 (strict verification)

**Verification Tasks:**
1. **Visual Grounding:** Compare extracted text and LaTeX against actual image content
2. **Consistency Check:** Verify LaTeX correctly represents the math in text
3. **Error Detection:** Identify mismatches, missing symbols, incorrect numbers/operators
4. **Correction Offering:** Provide corrected LaTeX only if clear (else null)

**Output:**
```json
{
  "step_id": 1,
  "verified_text": "...",
  "verified_latex": "...",     // Corrected if needed
  "confidence": 0.95,
  "issues": [],                // List of detected problems
  "error_type": "none|student_error|extraction_error"
}
```

**Error Classification:**
- `none` → Extraction matches image perfectly
- `student_error` → Handwriting/problem solving mistake (not OCR's fault)
- `extraction_error` → OCR misread the content

---

#### 5. **Confidence Fusion** (OCR/main_pipeline.py)
**Purpose:** Combine confidence scores from all agents into a final confidence

**Formula:**
```
For steps WITH math:
  final_conf = 0.3 × extractor_conf + 0.4 × sympy_conf + 0.3 × verifier_conf

For steps WITHOUT math:
  final_conf = 0.6 × extractor_conf + 0.4 × verifier_conf
```

**Gating Rules (confidence reduction):**
- If sympy_conf < 0.5 → max(final_conf, 0.5)
- If sympy_conf < 0.3 → max(final_conf, 0.3)
- If |sympy_conf - verifier_conf| > 0.5 → multiply by 0.7
- If verifier_conf < 0.5 AND has issues → min(final_conf, 0.4)

**Result:** Each step gets a final_confidence ∈ [0, 1]

---

### **PHASE 2: GRADING PIPELINE** (grading/grading_pipeline.py)

#### 1. **Input Resolution**
- Searches for OCR output in priority order:
  1. Explicit path passed as argument
  2. `../OCR/final_output.json` (from OCR pipeline)
  3. `../final_output.json` (project root)
  4. `./final_output.json` (local)

#### 2. **Base Score Computation** (grading/scoring_utils.py)

For each step:
```python
if error_type == "none":
  base_score = max_marks × final_confidence

elif error_type == "extraction_error":
  base_score = max_marks × max(0.4, final_confidence)  # Minimum 0.4

elif error_type == "student_error":
  base_score = max_marks × 0.2  # Low marks (not OCR's fault)
```

Default: max_marks = 2 points per step

---

#### 3. **Gemini Grading** (grading/gemini_grader.py)

**Model Used:** Gemma 4 (31B-IT)
**Temperature:** 0.2 (slightly flexible for nuanced evaluation)

**Process:**
1. **Build Input:** Prepare steps with base scores and error classifications
2. **Grade Each Step:**
   - Evaluate correctness using final_latex
   - Adjust base_score by ±20% max
   - Provide clear feedback
   
3. **Special Handling:**
   - `error_type = "none"` → Normal grading
   - `error_type = "student_error"` → Keep low marks
   - `error_type = "extraction_error"` → Partial marks (NEVER 0)

**Output:**
```json
{
  "total_score": 18,
  "max_score": 20,
  "step_grading": [
    {
      "step_id": 1,
      "text": "...",
      "final_latex": "...",
      "base_score": 2.0,
      "final_score": 1.8,
      "feedback": "..."
    }
  ],
  "overall_feedback": "Good work, minor algebraic issue in step 3"
}
```

---

### **PHASE 3: COMBINED REPORT**

Merges both pipelines:
```json
{
  "image": "path/to/image.jpg",
  "problem": "Solve for x: 2x + 3 = 7",
  "ocr_steps": [
    { step details from OCR pipeline }
  ],
  "grading": {
    "total_score": 18,
    "max_score": 20,
    "step_grading": [ ... ],
    "overall_feedback": "..."
  }
}
```

---

## Data Flow Summary

```
1. Image Input
   ↓
2. Preprocessing
   - Resize, denoise, enhance contrast, threshold, crop
   ↓
3. Extraction (LLM)
   - Extract text + LaTeX
   ↓
4. SymPy Validation
   - Check math syntax
   - Generate sympy_confidence
   ↓
5. Verification (LLM + Vision)
   - Cross-check against image
   - Classify errors (none/student/extraction)
   - Generate verifier_confidence
   ↓
6. Confidence Fusion
   - Combine all confidence scores
   - final_confidence = weighted average + gating
   ↓
7. Grading
   - Compute base scores
   - AI-based grading with feedback
   ↓
8. Combined Report
   - Merge OCR + grading results
```

---

## Key Features

### **1. Multi-Agent Architecture**
- Each agent specializes in one task
- Agents communicate via JSON structures
- Confidence scores enable multi-stage validation

### **2. Error Classification**
Distinguishes between:
- **Extraction errors** (OCR misread) → Partial credit
- **Student errors** (wrong math) → Low credit
- **No errors** (correct) → Full credit

### **3. Confidence Gating**
- Low SymPy confidence penalizes final score heavily
- Large verifier-sympy disagreements reduce confidence
- Prevents false positives from incorrect OCR

### **4. Vision-Based Verification**
- Uses LLM with image to catch OCR mistakes
- Cross-references text and math against actual image
- Corrects LaTeX when feasible

### **5. Symbolic Math Validation**
- Uses SymPy for mathematical syntax checking
- Handles equations, expressions, matrices
- Detects invalid operations (div by 0, etc.)

### **6. AI-Powered Grading**
- Uses Gemini to evaluate correctness
- Respects error classifications
- Provides detailed step-by-step feedback
- Prevents harsh penalties for extraction errors

---

## Dataset Structure

```
dataset/
├── data/
│   ├── train.json      # Training dataset
│   ├── val.json        # Validation dataset
│   ├── test.json       # Test dataset
│   └── images/         # Image files
```

Format (typical):
```json
{
  "id": "problem_001",
  "problem": "Solve for x: 2x + 3 = 7",
  "solution_steps": [
    {"step": 1, "text": "Subtract 3 from both sides", "latex": "2x = 4"},
    {"step": 2, "text": "Divide by 2", "latex": "x = 2"}
  ],
  "correct_answer": "x = 2",
  "image_path": "images/problem_001.jpg"
}
```

---

## Output Files Generated

| File | Location | Purpose |
|------|----------|---------|
| `processed.jpg` | OCR/ | Preprocessed image |
| `extraction_output.json` | OCR/ | Raw extraction results |
| `sympy_output.json` | OCR/ | SymPy validation results |
| `verifier_output.json` | OCR/ | Verification results |
| `final_output.json` | OCR/ | Complete OCR pipeline output |
| `grading_output.json` | grading/ | Grading results |
| `combined_output.json` | root | Final merged report |

---

## API Configuration

**Model:** Google Gemini (Gemma 4 31B-IT variant)
**Image Dimension Limits:**
- Preprocessing: max 1024px
- API submission: max 512px
- Quality: JPEG 90

**API Key:** Stored in `.env` file (not tracked in git)

---

## Execution Entry Point

**Main Script:** `run_all.py`

```python
python run_all.py <image_path>
```

**Execution Steps:**
1. Load `.env` for API key
2. Run OCR pipeline (saves to OCR/)
3. Run grading pipeline (saves to grading/)
4. Merge results to combined_output.json

---

## Summary

This is a **sophisticated multi-stage OCR + grading system** that:
- ✅ Extracts math from handwritten images
- ✅ Validates syntax symbolically
- ✅ Verifies content against images
- ✅ Automatically grades solutions
- ✅ Classifies errors intelligently
- ✅ Provides detailed feedback

The use of **multiple validation stages** (extraction, symbolic, visual) ensures high accuracy while the **error classification** system enables fair grading by distinguishing OCR errors from student mistakes.
