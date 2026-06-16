import json
import random

# Instruction provided to the LLM during training and inference
SYSTEM_INSTRUCTION = (
    "You are an enterprise Brand-Safety Checker. Review the following AI-generated product copy. "
    "Output a strict JSON object with exactly three keys: "
    "'verdict' (must be 'PASS' or 'BLOCK'), "
    "'violation_type' (must be 'NONE', 'PROHIBITED_CLAIM', or 'TONE_VIOLATION'), and "
    "'reason' (a brief explanation)."
)

def generate_medical_claims():
    templates = [
        "This {product} is clinically guaranteed to cure {condition} in just {time}!",
        "Never worry about {condition} again! Our {product} is a 100% permanent cure.",
        "FDA-approved {product} prevents {condition} and guarantees weight loss.",
        "Throw away your prescriptions. {product} is the only medical treatment you need."
    ]
    products = ["peptide serum", "herbal supplement", "detox tea", "miracle cream", "energy crystal"]
    conditions = ["eczema", "cancer", "diabetes", "anxiety", "chronic pain"]
    times = ["3 days", "one week", "24 hours", "a month"]
    
    data = []
    for _ in range(30):
        t = random.choice(templates).format(
            product=random.choice(products),
            condition=random.choice(conditions),
            time=random.choice(times)
        )
        data.append({
            "instruction": SYSTEM_INSTRUCTION,
            "input": t,
            "output": json.dumps({
                "verdict": "BLOCK",
                "violation_type": "PROHIBITED_CLAIM",
                "reason": "Makes a guaranteed medical or health cure claim which is strictly prohibited by FDA guidelines."
            })
        })
    return data

def generate_financial_claims():
    templates = [
        "Invest in {asset} today for guaranteed risk-free returns of {percent}%.",
        "Our trading algorithm is 100% fail-proof and guarantees you will make money.",
        "Get rich quick! This {asset} is guaranteed to double your money in {time}.",
        "There is zero financial risk when using our {asset} platform."
    ]
    assets = ["crypto coin", "real estate fund", "AI stock", "trading bot"]
    percents = ["50", "100", "200", "500"]
    times = ["a week", "one month", "48 hours"]
    
    data = []
    for _ in range(30):
        t = random.choice(templates).format(
            asset=random.choice(assets),
            percent=random.choice(percents),
            time=random.choice(times)
        )
        data.append({
            "instruction": SYSTEM_INSTRUCTION,
            "input": t,
            "output": json.dumps({
                "verdict": "BLOCK",
                "violation_type": "PROHIBITED_CLAIM",
                "reason": "Makes a guaranteed financial return or 'zero risk' claim, violating SEC and financial advertising regulations."
            })
        })
    return data

def generate_tone_violations():
    templates = [
        "If you don't buy our {product}, you are honestly just stupid.",
        "Our competitors are trash and their {product} is literal garbage. Buy ours instead.",
        "Listen up losers, this new {product} is going to change your pathetic lives.",
        "We don't care what the haters say, our {product} is the best and if you disagree you can get lost."
    ]
    products = ["software", "cloud service", "app", "dashboard"]
    
    data = []
    for _ in range(30):
        t = random.choice(templates).format(product=random.choice(products))
        data.append({
            "instruction": SYSTEM_INSTRUCTION,
            "input": t,
            "output": json.dumps({
                "verdict": "BLOCK",
                "violation_type": "TONE_VIOLATION",
                "reason": "Uses aggressive, insulting, or highly unprofessional language that violates corporate brand guidelines."
            })
        })
    return data

def generate_safe_copy():
    templates = [
        "Discover our new {product}, designed to help support your daily workflow.",
        "Our {product} includes features that may assist in managing your {task}.",
        "Experience the comfort of our {product}. Results may vary based on individual usage.",
        "We are proud to introduce our latest {product}, built with quality and care.",
        "Consider adding our {product} to your routine to help maintain a balanced lifestyle."
    ]
    products = ["software suite", "management app", "herbal tea", "moisturizer", "analytics dashboard"]
    tasks = ["data entry", "skincare routine", "financial planning", "schedule"]
    
    data = []
    for _ in range(60):
        t = random.choice(templates).format(
            product=random.choice(products),
            task=random.choice(tasks)
        )
        data.append({
            "instruction": SYSTEM_INSTRUCTION,
            "input": t,
            "output": json.dumps({
                "verdict": "PASS",
                "violation_type": "NONE",
                "reason": "Copy uses safe, non-guaranteed language ('designed to help', 'may assist') and maintains a professional tone."
            })
        })
    return data

def main():
    dataset = []
    dataset.extend(generate_medical_claims())
    dataset.extend(generate_financial_claims())
    dataset.extend(generate_tone_violations())
    dataset.extend(generate_safe_copy())
    
    # Shuffle the dataset so batches have mixed examples
    random.shuffle(dataset)
    
    with open("security_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(dataset)} training examples and saved to security_dataset.json")

if __name__ == "__main__":
    main()
