import random
from io import BytesIO
from PIL import Image
from torchvision import transforms

class RandomJPEGCompression:
    def __init__(self, p: float = 0.5, quality_range=(60, 95)):
        self.p = p
        self.quality_range = quality_range

    def __call__(self, image: Image.Image) -> Image.Image:
        if random.random() >= self.p:
            return image
        quality = random.randint(*self.quality_range)
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        return Image.open(buffer).convert('RGB')


def get_train_transform(image_size=(384, 384)):
    return transforms.Compose([
        transforms.RandomResizedCrop(image_size, scale=(0.75, 1.0), ratio=(0.9, 1.1)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.20, hue=0.05),
        transforms.RandomApply([transforms.GaussianBlur(kernel_size=(3, 7), sigma=(0.1, 2.0))], p=0.3),
        transforms.RandomApply([RandomJPEGCompression(p=1.0, quality_range=(60, 90))], p=0.35),
        transforms.RandomGrayscale(p=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def get_eval_transform(image_size=(384, 384)):
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def augment_image(image):
    """Legacy augmentation helper for numpy/CV2 pipelines."""
    if isinstance(image, Image.Image):
        pil_image = image
    else:
        pil_image = Image.fromarray(image)
    aug = get_train_transform(image_size=pil_image.size[::-1])
    return aug(pil_image)
