PARAMETER_KEYS = [
    "brightness_quality",
    "colorfulness_quality",
    "contrast_quality",
    "noise_quality",
    "sharpness_quality",
]

OVERALL_WEIGHT = 0.6
PARAMETERS_WEIGHT = 0.4
DELETE_THRESHOLD = 40


def create_batch_result(filename, scores):
    parameter_scores = [
        scores[key]
        for key in PARAMETER_KEYS
    ]

    parameters_average = sum(parameter_scores) / len(parameter_scores)

    combined_score = (
        scores["overall_quality"] * OVERALL_WEIGHT
        + parameters_average * PARAMETERS_WEIGHT
    )

    if combined_score < DELETE_THRESHOLD:
        decision = "delete"
        decision_label = "Кандидат на видалення"
    else:
        decision = "keep"
        decision_label = "Залишити"

    return {
        "filename": filename,
        "overall_score": scores["overall_quality"],
        "parameters_average": round(parameters_average, 2),
        "combined_score": round(combined_score, 2),
        "decision": decision,
        "decision_label": decision_label,
        "scores": scores,
    }