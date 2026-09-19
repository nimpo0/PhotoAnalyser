LOW_THRESHOLD = 45
MEDIUM_THRESHOLD = 65
DARK_PIXELS_LIMIT = 25
OVEREXPOSED_LIMIT = 8
BLUR_LAPLACIAN_LIMIT = 120
NOISE_LIMIT = 6.0
LOW_CONTRAST_LIMIT = 60
LOW_SATURATION_LIMIT = 15
HIGH_SATURATION_LIMIT = 55


PARAMETERS = [
    ("brightness_quality", "Яскравість"),
    ("colorfulness_quality", "Кольоровість"),
    ("contrast_quality", "Контраст"),
    ("noise_quality", "Якість щодо шуму"),
    ("sharpness_quality", "Різкість"),
]


def get_quality_level(score):
    if score < LOW_THRESHOLD:
        return "Потребує покращення"
    if score < MEDIUM_THRESHOLD:
        return "Можна покращити"
    return "Добра якість"


def _brightness_text(measurements, severity):
    dark = measurements["dark_pixels_percent"]
    bright = measurements["overexposed_pixels_percent"]
    strong = severity == "low"

    if dark > DARK_PIXELS_LIMIT and dark >= bright:
        if strong:
            return "Фото затемнене - спробуйте збільшити експозицію або зняти за кращого освітлення."
        return "Фото трохи темнувате — невелике підвищення яскравості не завадить."

    if bright > OVEREXPOSED_LIMIT and bright > dark:
        if strong:
            return "Кадр пересвітлений — зменшіть експозицію або уникайте прямого світла."
        return "Місцями трохи пересвітлено — варто злегка знизити яскравість."

    if strong:
        return "З яскравістю щось не так — спробуйте відкоригувати експозицію."
    return "Яскравість можна трохи підправити."


def _sharpness_text(measurements, severity):
    blurry = measurements["laplacian_variance"] < BLUR_LAPLACIAN_LIMIT
    strong = severity == "low"

    if blurry:
        if strong:
            return "Кадр розмитий — спробуйте стабілізацію, коротшу витримку або точніший фокус."
        return "Різкість трохи просідає — перевірте фокус перед наступним знімком."

    if strong:
        return "Фото могло б бути чіткішим — спробуйте перезняти без розмиття."
    return "Невелике підвищення різкості додасть деталям виразності."


def _noise_text(measurements, severity):
    noisy = measurements["noise_level"] > NOISE_LIMIT
    strong = severity == "low"

    if noisy:
        if strong:
            return "Помітний цифровий шум — спробуйте нижчий ISO або більше світла."
        return "У тінях трохи шумить — нижчий ISO допоможе."

    if strong:
        return "Варто зменшити шум на зображенні, особливо в темних ділянках."
    return "Невелике зменшення шуму трохи почистить картинку."


def _contrast_text(measurements, severity):
    flat = measurements["contrast_range"] < LOW_CONTRAST_LIMIT
    strong = severity == "low"

    if flat:
        if strong:
            return "Кадр виглядає пласким — світлі й темні ділянки злиті, підніміть контраст."
        return "Контрасту трохи бракує — це підкреслить деталі."

    if strong:
        return "Спробуйте підкоригувати контраст, щоб деталі виглядали чіткіше."
    return "Невелике коригування контрасту піде на користь."


def _colorfulness_text(measurements, severity):
    saturation = measurements["mean_saturation"]
    strong = severity == "low"

    if saturation < LOW_SATURATION_LIMIT:
        if strong:
            return "Кольори виглядають тьмяними — підвищена насиченість оживить кадр."
        return "Кольорам бракує глибини — невелика насиченість не завадить."

    if saturation > HIGH_SATURATION_LIMIT:
        if strong:
            return "Кольори перенасичені — знизьте насиченість для природнішого вигляду."
        return "Насиченість трохи завищена — варто її притишити."

    if strong:
        return "Спробуйте підкоригувати насиченість кольорів."
    return "Невелике коригування кольорів зробить кадр природнішим."


TEXT_BUILDERS = {
    "brightness_quality": _brightness_text,
    "colorfulness_quality": _colorfulness_text,
    "contrast_quality": _contrast_text,
    "noise_quality": _noise_text,
    "sharpness_quality": _sharpness_text,
}


def generate_recommendations(scores, measurements):
    parameters = []
    recommendations = []

    for key, label in PARAMETERS:
        score = scores[key]
        level = get_quality_level(score)
        parameters.append({"key": key, "label": label, "score": score, "level": level})

        if score < LOW_THRESHOLD:
            severity = "low"
        elif score < MEDIUM_THRESHOLD:
            severity = "medium"
        else:
            continue

        text = TEXT_BUILDERS[key](measurements, severity)
        recommendations.append({"parameter": label, "score": score, "text": text})

    recommendations.sort(key=lambda item: item["score"])
    recommendations = recommendations[:4]

    if recommendations:
        weak_parameters = ", ".join(item["parameter"].lower() for item in recommendations)
        summary = f"Параметри, які варто покращити: {weak_parameters}."
    else:
        summary = "Основні параметри фотографії мають добру якість. Значні виправлення не потрібні."

    return {
        "parameters": parameters,
        "recommendation_summary": summary,
        "recommendations": recommendations,
        "measurements": measurements,
    }