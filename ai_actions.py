from docling.document_converter import DocumentConverter
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

def model_preparation():
    filepath = os.path.join(os.path.dirname(__file__), "model")
    if not os.path.isdir(filepath):  
        print("Downloading Qwen3-0.6B as no model found")
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
        model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B")
        tokenizer.save_pretrained("./model")
        model.save_pretrained("./model")
        
def get_json(messages):
    tokenizer = AutoTokenizer.from_pretrained("./model")
    model = AutoModelForCausalLM.from_pretrained(
        "./model",
        device_map="auto",  
        torch_dtype="auto"  
    )
                
    text = tokenizer.apply_chat_template(
        messages,
        tokenize = False,
        add_generation_prompt = True,
        enable_thinking = False,
    )
                
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=32768
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 
    
    return tokenizer.decode(output_ids, skip_special_tokens=True).strip("\n")