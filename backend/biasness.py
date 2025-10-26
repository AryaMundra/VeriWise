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

def analyze_articles(articles: list, threshold: float = 0.7):
    for idx, article in enumerate(articles, start=1):
        label, score = predict_bias(article, threshold)
        print(f"\n--- Article {idx} ---")
        print(f"Preview: {article[:120]}...")
        print(f"Predicted Bias: {label}")
        print(f"Confidence: {score:.2%}")

articles = [
    # Neutral
    "Elizabeth Wellington is a writer for the Philadelphia Inquirer, frequently writing about fashion and style.Not far from the 2016 election, she wrote an article bashing Melania Trump for wearing a white dress for her RNC speech. Wellington felt that the white designer dress was a “scary statement,” and gave off a reminder that “in the G.O.P. white is always right.” So apparently wearing a white shirt - not a dark one - to a political convention is considered racist.But somehow, Wellington changed her mind only ten days later and decided that white was a decent, respectable color for a politician. Hillary Clinton appeared at the DNC not long afterwards wearing a plain-white formal shirt, strikingly similar to Melania’s but sans the puffy sleeves.",


    "Wikipedia has become a powerful weapon in the left’s political arsenal. Initially launched to democratize access to information, it has debased itself through partisanship.No longer a straightforward source of facts, Wikipedia today is pure left-wing propaganda — and its intense campaign against Vice President JD Vance is just the latest example of its bias.The Media Research Center’s Free Speech America division has previously reported how Wikipedia’s editors aggressively deployed the platform against nearly all of President Donald Trump’s high-level Cabinet nominees, including now-Defense Secretary Pete Hegseth and FBI Director Kash Patel, ahead of their Senate confirmation hearings.",

    "Michael Smuss, a survivor of the Warsaw Ghetto in Poland who resisted the Nazis, has died aged 99 in Israel.He joined the ghetto uprising as a teenager in 1943, helping to make petrol bombs. Taken prisoner, he survived concentration camps and a death march before the end of World War II.After the war, he became an artist and Holocaust educator. The embassies of Germany and Poland in Israel paid tribute to him on social media.He repeatedly risked his life during the Holocaust, fighting for survival and helping other prisoners in the Warsaw Ghetto – even after he was captured by the Nazis and deported to concentration camps, the German embassy stated on X."
]

analyze_articles(articles, threshold=0.6)


