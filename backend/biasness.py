from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

MODEL_NAME = "himel7/bias-detector"
print(f"Loading model: {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    framework="pt"  
)

LABEL_MAPPING = {
    "LABEL_0": "Neutral",
    "LABEL_1": "Biased"
}

def predict_bias(article_text: str, threshold: float = 0.7):
    """
    Predicts if an article is Biased or Neutral.
    Confidence below threshold for Biased is treated as Neutral.
    """
    result = classifier(article_text)[0]
    raw_label = result['label']
    score = result['score']

    label = LABEL_MAPPING.get(raw_label, raw_label)

    if label == "Biased" and score < threshold:
        label = "Neutral"
    
    return label, score




