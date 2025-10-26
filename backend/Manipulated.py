import torch
from transformers import AutoImageProcessor, SiglipForImageClassification
from PIL import Image

model_name = "prithivMLmods/Deepfake-Detect-Siglip2"
model = SiglipForImageClassification.from_pretrained(model_name)
processor = AutoImageProcessor.from_pretrained(model_name)

# Label mapping
labels = {
    "0": "Fake",
    "1": "Real"
}

def detect_deepfake(image_path):
    """
    Detects if an image is manipulated (deepfake) or authentic (real)
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Dictionary with detection results
    """

    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()
    
    # Get predictions
    fake_score = probs[0]
    real_score = probs[1]
    
    predicted_class = "Fake" if fake_score > real_score else "Real"
    confidence = max(fake_score, real_score)
    
    return {
        "prediction": predicted_class,
        "confidence": confidence,
        "fake_score": fake_score,
        "real_score": real_score,
        "is_manipulated": predicted_class == "Fake"
    }

