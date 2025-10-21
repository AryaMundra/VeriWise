import torch
from transformers import AutoImageProcessor, SiglipForImageClassification
from PIL import Image

# Load model and processor
model_name = "prithivMLmods/Mirage-Photo-Classifier"
model = SiglipForImageClassification.from_pretrained(model_name)
processor = AutoImageProcessor.from_pretrained(model_name)

# Label mapping
labels = {
    "0": "Real",
    "1": "Fake"
}

def classify_image(image_path):
    """
    Classifies a single image as Real or AI-generated (Fake)
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Dictionary with prediction scores
    """
    # Load and preprocess image
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    
    # Make prediction
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()
    
    # Format results
    predictions = {labels[str(i)]: round(probs[i], 4) for i in range(len(probs))}
    predicted_class = max(predictions, key=predictions.get)
    
    return {
        "predicted_class": predicted_class,
        "confidence": predictions[predicted_class],
        "all_scores": predictions
    }

# Example usage
if __name__ == "__main__":
    result = classify_image("Gemini_Generated_Image_vdcu63vdcu63vdcu.png")
    print(f"Prediction: {result['predicted_class']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Scores: {result['all_scores']}")
