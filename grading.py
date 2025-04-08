# grading.py
import pdfplumber
import pandas as pd
import re
import sys

def parse_answer_key(pdf_path):
    """Parser for answer key with (*) and (4) markers"""
    answers = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_question = 0
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        line = line.strip()
                        
                        # Detect question numbers
                        q_match = re.match(r"^(\d+)[\.\)]?\s*", line)
                        if q_match:
                            current_question = int(q_match.group(1))
                            continue
                            
                        # Answer key parsing
                        if re.search(r'\(\s*[\*4]\s*\)', line):
                            answer = re.split(r'[-–—]', line, 1)[-1].split('(')[0].strip()
                            answers[current_question] = answer
    except FileNotFoundError:
        print(f"Error: File {pdf_path} not found!")
        sys.exit(1)
    return answers

def parse_gpt(pdf_path):
    """Special parser for GPT's dual format"""
    answers = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_question = 0
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        line = line.strip()
                        
                        # Detect question number
                        q_match = re.match(r"^(\d+)[\.\)]?\s*", line)
                        if q_match:
                            current_question = int(q_match.group(1))
                            if current_question <= 80 and ':' in line:
                                answer = line.split(':', 1)[1].strip()
                                answers[current_question] = answer
                            continue
                            
                        # Handle Q81-500 Answer: format
                        if current_question > 80 and "Answer:" in line:
                            answer = line.split("Answer:", 1)[1].strip()
                            answers[current_question] = answer
    except FileNotFoundError:
        print(f"Error: File {pdf_path} not found!")
        sys.exit(1)
    return answers

def parse_other_models(pdf_path):
    """Parser for models with simple numbered answers"""
    answers = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_question = 0
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        line = line.strip()
                        q_match = re.match(r"^(\d+)[\.\)]?\s*", line)
                        if q_match:
                            current_question = int(q_match.group(1))
                            answer = line.split(f"{current_question}.", 1)[-1].strip()
                            answers[current_question] = answer
    except FileNotFoundError:
        print(f"Error: File {pdf_path} not found!")
        sys.exit(1)
    return answers

def calculate_scores(answer_key, model_answers):
    """Universal scoring function"""
    scores = {}
    for q in range(1, 501):
        key_ans = answer_key.get(q, "").strip()
        model_ans = model_answers.get(q, "").strip()
        
        # Consistent normalization
        clean = lambda x: re.sub(r'[^\w]', '', x).lower()
        scores[q] = 100 if clean(key_ans) == clean(model_ans) else 0
        
    return scores

if __name__ == "__main__":
    # Load answer key and models
    answer_key = parse_answer_key("answer_key.pdf")
    models = {
        "GPT": parse_gpt("gpt.pdf"),
        "Grok": parse_other_models("grok.pdf"),
        "Bencao": parse_other_models("bencao.pdf"),
        "Claude": parse_other_models("claude.pdf"),
        "DeepSeek": parse_other_models("deepseek.pdf"),
        "Gemini": parse_other_models("gemini.pdf")
    }
    
    # Calculate and validate scores
    results = {}
    for model_name, answers in models.items():
        results[model_name] = calculate_scores(answer_key, answers)
        missing = [q for q in range(1, 501) if q not in answers]
        if missing:
            print(f"⚠️ {model_name} missing answers for questions: {missing}")
    
    # Build final dataframe
    df = pd.DataFrame({"Question": list(range(1, 501))})
    for model_name, scores in results.items():
        df[model_name] = list(scores.values())
    
    # Add averages
    averages = {model: df[model].mean().round(2) for model in models}
    avg_row = pd.DataFrame({"Question": ["Average"]} | averages)
    df = pd.concat([df, avg_row], ignore_index=True)
    
    # Save results
    df.to_excel("results.xlsx", index=False)
    print("✅ All scores saved with proper formatting!")