from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from app.batch_analysis import create_batch_result
from app.model_service import PhotoQualityModel
from app.recommendations import generate_recommendations, get_quality_level
from app.technical_metrics import analyze_technical_metrics


FRONTEND_DIRECTORY = Path(__file__).resolve().parent / "static"

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_BATCH_FILES = 30


app = FastAPI(title="Photo Quality Analyzer")
model_service = None


@app.on_event("startup")
def load_model():
    global model_service
    model_service = PhotoQualityModel()


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIRECTORY / "index.html")


async def read_uploaded_image(file):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        await file.close()
        raise HTTPException(400, "Завантажте зображення у форматі JPG, PNG або WEBP.")

    image_bytes = await file.read()
    await file.close()

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(400, "Розмір одного файлу не повинен перевищувати 10 МБ.")

    try:
        image = Image.open(BytesIO(image_bytes))
        image.load()
        return image
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "Не вдалося прочитати завантажене зображення.")


@app.post("/api/analyze")
async def analyze_photo(file: UploadFile = File(...)):
    image = await read_uploaded_image(file)

    scores = model_service.predict(image)
    measurements = analyze_technical_metrics(image)
    analysis = generate_recommendations(scores, measurements)

    return {
        "filename": file.filename,
        "overall_score": scores["overall_quality"],
        "overall_level": get_quality_level(scores["overall_quality"]),
        **analysis,
    }


@app.post("/api/analyze-batch")
async def analyze_batch(files: list[UploadFile] = File(...)):
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(400, "За один раз можна завантажити не більше 30 фотографій.")

    results = []
    errors = []

    for file in files:
        try:
            image = await read_uploaded_image(file)
            scores = model_service.predict(image)
            results.append(create_batch_result(filename=file.filename, scores=scores))
        except HTTPException as error:
            errors.append({"filename": file.filename, "error": error.detail})

    keep_count = sum(result["decision"] == "keep" for result in results)
    delete_count = sum(result["decision"] == "delete" for result in results)

    return {
        "received_count": len(files),
        "analyzed_count": len(results),
        "keep_count": keep_count,
        "delete_count": delete_count,
        "error_count": len(errors),
        "results": results,
        "errors": errors,
    }


app.mount("/static", StaticFiles(directory=FRONTEND_DIRECTORY), name="static")