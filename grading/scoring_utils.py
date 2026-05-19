# scoring_utils.py

def compute_step_score(step, max_marks=2):
    conf = step.get("final_confidence", 0.5)
    error = step.get("error_type", "none")

    if error == "none":
        return round(max_marks * conf, 2)

    elif error == "extraction_error":
        return round(max_marks * max(0.4, conf), 2)

    elif error == "student_error":
        return round(max_marks * 0.2, 2)

    return 0