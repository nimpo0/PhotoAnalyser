from pathlib import Path
import torch
import torch.nn as nn
from PIL import ImageOps
from torchvision.models import resnet18
from data_utils import IMAGE_SIZE, TARGET_COLUMNS, build_transforms


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "models"
    / "resnet_fine_tuning_best.pt"
)

class PhotoQualityModel:
    def __init__(self, model_path=MODEL_PATH):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = self._create_model()

        checkpoint = torch.load(
            model_path,
            map_location=self.device,
            weights_only=True,
        )

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        _, self.transform = build_transforms(image_size=IMAGE_SIZE)

        print("Модель завантажена:", model_path)
        print("Пристрій:", self.device)

    def _create_model(self):
        model = resnet18(weights=None)
        number_of_features = model.fc.in_features

        model.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(number_of_features, len(TARGET_COLUMNS)),
            nn.Sigmoid(),
        )

        return model

    def predict(self, image):
        image = ImageOps.exif_transpose(image).convert("RGB")
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            predictions = self.model(image_tensor)[0] * 100.0

        predictions = predictions.cpu().numpy()

        return {
            target: round(float(score), 2)
            for target, score in zip(TARGET_COLUMNS, predictions)
        }