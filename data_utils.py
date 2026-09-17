from pathlib import Path
import random
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

RANDOM_STATE = 42
IMAGE_SIZE = 224
BATCH_SIZE = 16
NUM_WORKERS = 0

TRAIN_SIZE = 3000
VALIDATION_SIZE = 600
TEST_SIZE = 600

TARGET_COLUMNS = [
    "overall_quality", "brightness_quality", "colorfulness_quality",
    "contrast_quality", "noise_quality", "sharpness_quality",
]

TARGET_NAMES = [
    "Загальна якість", "Яскравість", "Кольоровість",
    "Контраст", "Якість щодо шуму", "Різкість",
]

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def seed_everything(seed=RANDOM_STATE):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def prepare_splits(manifest, debug_mode=True, random_state=RANDOM_STATE):
    required_columns = ["image_name", "split"] + TARGET_COLUMNS
    missing_columns = [c for c in required_columns if c not in manifest.columns]
    if missing_columns:
        raise ValueError(f"У manifest відсутні колонки: {missing_columns}")

    if manifest["image_name"].isna().any():
        raise ValueError("У manifest є пропущені назви фото.")

    split_names = ("train", "validation", "test")
    if not manifest["split"].isin(split_names).all():
        raise ValueError("Колонка split повинна містити лише 'train', 'validation' або 'test'.")

    split_dataframes = {}
    for split_name in split_names:
        dataframe = manifest[manifest["split"] == split_name].copy().reset_index(drop=True)
        if dataframe.empty:
            raise ValueError(f"Вибірка '{split_name}' порожня.")
        split_dataframes[split_name] = dataframe

    image_names = {
        split_name: set(dataframe["image_name"].astype(str))
        for split_name, dataframe in split_dataframes.items()
    }
    for first, second in (("train", "validation"), ("train", "test"), ("validation", "test")):
        overlap = image_names[first] & image_names[second]
        if overlap:
            raise ValueError(f"Між '{first}' і '{second}' є спільні фото: {sorted(overlap)[:5]}")

    if debug_mode:
        limits = {"train": TRAIN_SIZE, "validation": VALIDATION_SIZE, "test": TEST_SIZE}
        for split_name, limit in limits.items():
            dataframe = split_dataframes[split_name]
            split_dataframes[split_name] = dataframe.sample(
                n=min(limit, len(dataframe)), random_state=random_state
            ).reset_index(drop=True)

    return split_dataframes["train"], split_dataframes["validation"], split_dataframes["test"]


def build_transforms(image_size=IMAGE_SIZE):
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size), antialias=True),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    evaluation_transform = transforms.Compose([
        transforms.Resize((image_size, image_size), antialias=True),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    return train_transform, evaluation_transform


class PhotoQualityDataset(Dataset):

    def __init__(self, dataframe, images_directory, target_columns=None, transform=None):
        self.dataframe = dataframe.copy().reset_index(drop=True)
        self.images_directory = Path(images_directory)
        self.target_columns = list(TARGET_COLUMNS if target_columns is None else target_columns)
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index):
        row = self.dataframe.iloc[index]
        image_name = str(row["image_name"])
        image_path = self.images_directory / image_name

        with Image.open(image_path) as image:
            image = image.convert("RGB")
            if self.transform is not None:
                image = self.transform(image)

        target_values = row[self.target_columns].to_numpy(dtype=np.float32) / 100.0
        targets = torch.tensor(target_values, dtype=torch.float32)

        return image, targets, image_name


def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % (2 ** 32)
    np.random.seed(worker_seed)
    random.seed(worker_seed)


def create_loaders(
    train_dataset, validation_dataset, test_dataset, device,
    batch_size=BATCH_SIZE, num_workers=NUM_WORKERS, random_state=RANDOM_STATE,
):
    device = torch.device(device)

    loader_generator = torch.Generator()
    loader_generator.manual_seed(random_state)

    loader_options = {
        "batch_size": batch_size,
        "num_workers": num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": num_workers > 0,
        "worker_init_fn": seed_worker,
    }

    train_loader = DataLoader(train_dataset, shuffle=True, generator=loader_generator, **loader_options)
    validation_loader = DataLoader(validation_dataset, shuffle=False, **loader_options)
    test_loader = DataLoader(test_dataset, shuffle=False, **loader_options)

    return train_loader, validation_loader, test_loader