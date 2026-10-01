import requests
import os
import argparse

# --- CONFIGURATION ---
# 400 lines is the safe limit for a 4GB VRAM GPU. 
# It prevents an Out-Of-Memory (OOM) crash during the live demo.
MAX_LINES = 400 
ALLOWED_EXTENSIONS = ['.py', '.js', '.ts', '.java', '.cpp', '.c']

# Use "qwen2.5-coder:3b" for the hackathon.
# Use "gemma3:4b" for testing beforehand if you want a smarter, slower model.
CURRENT_MODEL = "qwen2.5-coder:3b" 
# ---------------------

def get_project_context(start_path="."):
    """Recursively reads files, stopping exactly at MAX_LINES."""
    context_string = ""
    total_lines = 0
    
    for root, dirs, files in os.walk(start_path):
        # Skip hidden folders and virtual environments to save RAM
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]
        
        for file in files:
            if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                        # Only take what we need to hit the 400 line limit
                        lines_to_take = lines[:MAX_LINES - total_lines]
                        content = "".join(lines_to_take)
                        
                        file_block = f"\n--- FILE: {file_path} ---\n{content}\n"
                        context_string += file_block
                        total_lines += len(lines_to_take)
                        
                        if total_lines >= MAX_LINES:
                            print(f"⚠️ {MAX_LINES}-line limit reached. Stopping context load to protect VRAM.")
                            return context_string
                except Exception:
                    pass # Ignore files we can't read
                    
    return context_string if context_string else "No project code files found."

def query_ollama(error_message, project_context):
    url = "http://localhost:11434/api/generate"
    
    # Strict prompt to force the model to output ONLY the fix
    prompt = f"""
    You are an expert software engineer. 
    A user encountered this terminal error:
    "{error_message}"
    
    Here is the context of their project (truncated to fit memory limits):
    {project_context}
    
    Analyze the error against the project code. Output ONLY the exact code snippet or terminal command needed to fix the error.
    Do NOT output explanations. Do NOT output markdown formatting.
    
    Fix:
    """
    
    payload = {
        "model": CURRENT_MODEL, 
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()["response"].strip()
    except Exception as e:
        return f"Error connecting to Ollama: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix terminal errors with local AI and project context.")
    parser.add_argument("--error", type=str, required=True, help="The error message to fix")
    parser.add_argument("--project", type=str, default=".", help="Path to the project root folder (defaults to current folder)")
    args = parser.parse_args()
    
    print(f"📂 Loading project context (max {MAX_LINES} lines)...")
    context = get_project_context(args.project)
    print(f"✅ Context loaded. Analyzing error with {CURRENT_MODEL}...")
    
    fix = query_ollama(args.error, context)
    print(f"\n--- SUGGESTED FIX ---\n{fix}")