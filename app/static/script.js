const singleModeButton = document.querySelector("#single-mode-button");
const batchModeButton = document.querySelector("#batch-mode-button");
const singleMode = document.querySelector("#single-mode");
const batchMode = document.querySelector("#batch-mode");

const photoInput = document.querySelector("#photo-input");
const uploadArea = document.querySelector("#upload-area");
const previewBlock = document.querySelector("#preview-block");
const imagePreview = document.querySelector("#image-preview");
const fileName = document.querySelector("#file-name");
const changePhotoButton = document.querySelector("#change-photo");
const analyzeButton = document.querySelector("#analyze-button");
const loading = document.querySelector("#loading");
const errorMessage = document.querySelector("#error-message");
const results = document.querySelector("#results");

const batchPhotoInput = document.querySelector("#batch-photo-input");
const batchUploadArea = document.querySelector("#batch-upload-area");
const batchPreviewBlock = document.querySelector("#batch-preview-block");
const batchCount = document.querySelector("#batch-count");
const batchFileList = document.querySelector("#batch-file-list");
const changeBatchPhotosButton = document.querySelector("#change-batch-photos");
const analyzeBatchButton = document.querySelector("#analyze-batch-button");
const batchLoading = document.querySelector("#batch-loading");
const batchErrorMessage = document.querySelector("#batch-error-message");
const batchResults = document.querySelector("#batch-results");
const batchAnalyzedCount = document.querySelector("#batch-analyzed-count");
const batchKeepCount = document.querySelector("#batch-keep-count");
const batchDeleteCount = document.querySelector("#batch-delete-count");
const batchResultList = document.querySelector("#batch-result-list");

const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
const maxFileSize = 10 * 1024 * 1024;
const maxBatchFiles = 30;

let selectedFile = null;
let previewUrl = null;
let selectedBatchFiles = [];
let batchPreviewEntries = [];


function scoreClass(score) {
    if (score < 45) return "low";
    if (score < 65) return "medium";
    return "good";
}


function validatePhoto(file) {
    if (!allowedTypes.includes(file.type)) {
        return "Виберіть зображення у форматі JPG, PNG або WEBP.";
    }
    if (file.size > maxFileSize) {
        return `Файл «${file.name}» перевищує дозволені 10 МБ.`;
    }
    return null;
}


function formatFileSize(size) {
    return `${(size / 1024 / 1024).toFixed(1)} МБ`;
}


function setupPhotoPicker(area, input) {
    const openPicker = () => {
        input.value = "";
        input.click();
    };
    area.addEventListener("click", openPicker);
    return openPicker;
}


function setupDragAndDrop(area, onDrop) {
    ["dragenter", "dragover"].forEach((eventName) => {
        area.addEventListener(eventName, (event) => {
            event.preventDefault();
            area.classList.add("dragging");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        area.addEventListener(eventName, (event) => {
            event.preventDefault();
            area.classList.remove("dragging");
        });
    });

    area.addEventListener("drop", (event) => onDrop(event.dataTransfer.files));
}


function setMode(mode) {
    const isSingleMode = mode === "single";

    singleMode.classList.toggle("hidden", !isSingleMode);
    batchMode.classList.toggle("hidden", isSingleMode);
    singleModeButton.classList.toggle("active", isSingleMode);
    batchModeButton.classList.toggle("active", !isSingleMode);
    singleModeButton.setAttribute("aria-selected", String(isSingleMode));
    batchModeButton.setAttribute("aria-selected", String(!isSingleMode));
}

singleModeButton.addEventListener("click", () => setMode("single"));
batchModeButton.addEventListener("click", () => setMode("batch"));


function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function hideError() {
    errorMessage.classList.add("hidden");
}


function selectPhoto(file) {
    hideError();
    results.classList.add("hidden");

    const validationError = validatePhoto(file);
    if (validationError) {
        showError(validationError);
        return;
    }

    selectedFile = file;
    analyzeButton.disabled = false;

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);

    imagePreview.src = previewUrl;
    fileName.textContent = file.name;

    uploadArea.classList.add("hidden");
    previewBlock.classList.remove("hidden");
}


function renderResults(data) {
    const overallValue = document.querySelector("#overall-value");
    const overallScore = document.querySelector("#overall-score");
    const overallLevel = document.querySelector("#overall-level");
    const parameterList = document.querySelector("#parameter-list");
    const recommendationSummary = document.querySelector("#recommendation-summary");
    const recommendationList = document.querySelector("#recommendation-list");

    const overallClass = scoreClass(data.overall_score);
    const scoreColors = { good: "#2c9b67", medium: "#d89421", low: "#d95d5d" };

    overallValue.textContent = data.overall_score.toFixed(1);
    overallLevel.textContent = data.overall_level;
    overallLevel.className = `overall-level ${overallClass}`;
    overallScore.style.setProperty("--score", data.overall_score);
    overallScore.style.setProperty("--score-color", scoreColors[overallClass]);

    parameterList.replaceChildren();

    data.parameters.forEach((parameter) => {
        const colorClass = scoreClass(parameter.score);

        const item = document.createElement("div");
        item.className = "parameter-item";

        const heading = document.createElement("div");
        heading.className = "parameter-heading";

        const label = document.createElement("span");
        label.textContent = parameter.label;

        const score = document.createElement("span");
        score.className = colorClass;
        score.textContent = parameter.score.toFixed(1);

        const track = document.createElement("div");
        track.className = "progress-track";

        const fill = document.createElement("div");
        fill.className = `progress-fill ${colorClass}`;
        fill.style.width = `${parameter.score}%`;

        const level = document.createElement("p");
        level.className = "parameter-level";
        level.textContent = parameter.level;

        heading.append(label, score);
        track.append(fill);
        item.append(heading, track, level);
        parameterList.append(item);
    });

    recommendationSummary.textContent = data.recommendation_summary;
    recommendationList.replaceChildren();

    if (data.recommendations.length === 0) {
        const message = document.createElement("p");
        message.className = "success-message";
        message.textContent = "Фотографія не потребує значних технічних виправлень.";
        recommendationList.append(message);
    } else {
        data.recommendations.forEach((recommendation) => {
            const item = document.createElement("div");
            item.className = "recommendation-item";

            const title = document.createElement("strong");
            title.textContent = `${recommendation.parameter}: ${recommendation.score.toFixed(1)}`;

            const text = document.createElement("p");
            text.textContent = recommendation.text;

            item.append(title, text);
            recommendationList.append(item);
        });
    }

    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: "smooth", block: "start" });
}


async function analyzePhoto() {
    if (!selectedFile) return;

    hideError();
    results.classList.add("hidden");
    loading.classList.remove("hidden");
    analyzeButton.disabled = true;

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
        const response = await fetch("/api/analyze", { method: "POST", body: formData });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Не вдалося проаналізувати фото.");
        }

        renderResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        loading.classList.add("hidden");
        analyzeButton.disabled = false;
    }
}


const openSinglePhotoPicker = setupPhotoPicker(uploadArea, photoInput);
changePhotoButton.addEventListener("click", openSinglePhotoPicker);
analyzeButton.addEventListener("click", analyzePhoto);

photoInput.addEventListener("change", () => {
    if (photoInput.files.length > 0) selectPhoto(photoInput.files[0]);
});

setupDragAndDrop(uploadArea, (files) => {
    if (files.length > 0) selectPhoto(files[0]);
});


function showBatchError(message) {
    batchErrorMessage.textContent = message;
    batchErrorMessage.classList.remove("hidden");
}

function hideBatchError() {
    batchErrorMessage.classList.add("hidden");
}


function clearBatchPreviewUrls() {
    batchPreviewEntries.forEach((entry) => URL.revokeObjectURL(entry.url));
    batchPreviewEntries = [];
}


function renderBatchSelection() {
    clearBatchPreviewUrls();
    batchFileList.replaceChildren();

    selectedBatchFiles.forEach((file) => {
        const url = URL.createObjectURL(file);
        batchPreviewEntries.push({ file, url });

        const item = document.createElement("div");
        item.className = "batch-file-item";

        const image = document.createElement("img");
        image.src = url;
        image.alt = file.name;

        const name = document.createElement("strong");
        name.textContent = file.name;
        name.title = file.name;

        const size = document.createElement("span");
        size.textContent = formatFileSize(file.size);

        item.append(image, name, size);
        batchFileList.append(item);
    });

    batchCount.textContent = selectedBatchFiles.length;
    batchUploadArea.classList.add("hidden");
    batchPreviewBlock.classList.remove("hidden");
    analyzeBatchButton.disabled = false;
}


function selectBatchPhotos(fileList) {
    hideBatchError();
    batchResults.classList.add("hidden");

    const files = Array.from(fileList);
    if (files.length === 0) return;

    if (files.length > maxBatchFiles) {
        showBatchError("За один раз можна вибрати не більше 30 фотографій.");
        return;
    }

    for (const file of files) {
        const validationError = validatePhoto(file);
        if (validationError) {
            showBatchError(validationError);
            return;
        }
    }

    selectedBatchFiles = files;
    renderBatchSelection();
}


function findBatchPreview(filename) {
    const entry = batchPreviewEntries.find((previewEntry) => previewEntry.file.name === filename);
    return entry ? entry.url : null;
}


function createBatchResultCard(result) {
    const card = document.createElement("div");
    card.className = "batch-result-card";

    const previewSource = findBatchPreview(result.filename);

    if (previewSource) {
        const image = document.createElement("img");
        image.className = "batch-result-image";
        image.src = previewSource;
        image.alt = result.filename;
        card.append(image);
    } else {
        const imagePlaceholder = document.createElement("div");
        imagePlaceholder.className = "batch-result-image";
        card.append(imagePlaceholder);
    }

    const info = document.createElement("div");
    info.className = "batch-result-info";

    const name = document.createElement("strong");
    name.className = "batch-result-name";
    name.textContent = result.filename;
    name.title = result.filename;

    const details = document.createElement("p");
    details.className = "batch-result-details";
    details.textContent =
        `Загальна оцінка: ${result.overall_score.toFixed(1)} · ` +
        `Середнє параметрів: ${result.parameters_average.toFixed(1)}`;

    info.append(name, details);

    const decision = document.createElement("div");
    decision.className = "batch-result-decision";

    const decisionClass = result.decision === "keep" ? "keep" : "delete";

    const score = document.createElement("strong");
    score.className = `batch-result-score ${decisionClass}`;
    score.textContent = result.combined_score.toFixed(1);

    const badge = document.createElement("span");
    badge.className = `decision-badge ${decisionClass}`;
    badge.textContent = result.decision_label;

    decision.append(score, badge);
    card.append(info, decision);
    return card;
}


function renderBatchResults(data) {
    batchAnalyzedCount.textContent = data.analyzed_count;
    batchKeepCount.textContent = data.keep_count;
    batchDeleteCount.textContent = data.delete_count;

    batchResultList.replaceChildren();

    const sortedResults = [...data.results].sort(
        (first, second) => first.combined_score - second.combined_score
    );

    sortedResults.forEach((result) => {
        batchResultList.append(createBatchResultCard(result));
    });

    data.errors.forEach((error) => {
        const errorItem = document.createElement("div");
        errorItem.className = "batch-error-item";
        errorItem.textContent = `${error.filename}: ${error.error}`;
        batchResultList.append(errorItem);
    });

    batchResults.classList.remove("hidden");
    batchResults.scrollIntoView({ behavior: "smooth", block: "start" });
}


async function analyzeBatch() {
    if (selectedBatchFiles.length === 0) return;

    hideBatchError();
    batchResults.classList.add("hidden");
    batchLoading.classList.remove("hidden");
    analyzeBatchButton.disabled = true;

    const formData = new FormData();
    selectedBatchFiles.forEach((file) => formData.append("files", file));

    try {
        const response = await fetch("/api/analyze-batch", { method: "POST", body: formData });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Не вдалося проаналізувати фотографії.");
        }

        renderBatchResults(data);
    } catch (error) {
        showBatchError(error.message);
    } finally {
        batchLoading.classList.add("hidden");
        analyzeBatchButton.disabled = false;
    }
}


const openBatchPhotoPicker = setupPhotoPicker(batchUploadArea, batchPhotoInput);
changeBatchPhotosButton.addEventListener("click", openBatchPhotoPicker);
analyzeBatchButton.addEventListener("click", analyzeBatch);

batchPhotoInput.addEventListener("change", () => {
    selectBatchPhotos(batchPhotoInput.files);
});

setupDragAndDrop(batchUploadArea, selectBatchPhotos);


window.addEventListener("beforeunload", () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    clearBatchPreviewUrls();
});