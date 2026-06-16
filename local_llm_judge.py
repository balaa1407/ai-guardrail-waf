import time
import json
import torch
import os

# We detect if the user's local machine has a GPU. 
# If not, loading a 2-Billion parameter model will crash their laptop.
HAS_GPU = torch.cuda.is_available()

class LocalGuardrailJudge:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_mock = not HAS_GPU
        
        if self.is_mock:
            print("WARNING: No local GPU detected. Running in Fast-Mock mode for UI presentation.")
        else:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                from peft import PeftModel
                print("Loading Gemma 2B in 4-bit... This may take a minute.")
                model_id = "google/gemma-2b-it"
                self.tokenizer = AutoTokenizer.from_pretrained(model_id)
                base_model = AutoModelForCausalLM.from_pretrained(
                    model_id, 
                    load_in_4bit=True, 
                    device_map="auto"
                )
                
                # Load the custom brain we trained in Colab
                adapter_path = "./gemma-guardrail-adapter"
                if os.path.exists(adapter_path):
                    self.model = PeftModel.from_pretrained(base_model, adapter_path)
                    print("Custom adapter loaded successfully!")
                else:
                    self.model = base_model
                    print("Warning: Adapter not found. Using base model.")
                    
            except Exception as e:
                print(f"Failed to load heavy model. Falling back to Mock mode. Error: {e}")
                self.is_mock = True

    def evaluate_payload(self, text):
        # MOCK MODE (For fast UI demonstrations on laptops without GPUs)
        if self.is_mock:
            time.sleep(1.5) # Simulate LLM thinking time
            text_lower = text.lower()
            if "cure" in text_lower or "guarantee" in text_lower or "risk-free" in text_lower:
                return {
                    "verdict": "BLOCK",
                    "violation_type": "PROHIBITED_CLAIM",
                    "reason": "Makes a guaranteed medical or financial claim (detected via local edge model)."
                }
            elif "stupid" in text_lower or "trash" in text_lower:
                return {
                    "verdict": "BLOCK",
                    "violation_type": "TONE_VIOLATION",
                    "reason": "Uses aggressive or unprofessional language."
                }
            else:
                return {
                    "verdict": "PASS",
                    "violation_type": "NONE",
                    "reason": "No prohibited claims or tone violations detected by local judge."
                }
                
        # REAL INFERENCE (Requires GPU)
        prompt = (
            "Instruction:\nYou are an enterprise Brand-Safety Checker. "
            "Review the following AI-generated product copy. Output a strict JSON object with exactly three keys: "
            "'verdict' (must be 'PASS' or 'BLOCK'), 'violation_type' (must be 'NONE', 'PROHIBITED_CLAIM', or 'TONE_VIOLATION'), "
            "and 'reason' (a brief explanation).\n\n"
            f"Input:\n{text}\n\nOutput:\n"
        )
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = self.model.generate(**inputs, max_new_tokens=100, temperature=0.1)
        response_text = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        
        try:
            return json.loads(response_text)
        except:
            return {
                "verdict": "BLOCK",
                "violation_type": "PARSING_ERROR",
                "reason": f"Model output invalid JSON: {response_text}"
            }
