#!/usr/bin/env python3
import os
import sys
import json
import base64
import time
import re
import requests
import argparse

def get_images_from_dir(directory, count=2):
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return []
    
    # Get all jpg/jpeg/png files
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files.sort()  # Sort to ensure deterministic selection
    return files[:count]

def parse_llm_response(response_text):
    """
    Parse the LLM response to extract the mushroom size.
    Handles:
    1. Valid JSON format: {"size": "small"} or {"size": "large"}
    2. Markdown wrapped JSON: ```json {"size": "small"} ```
    3. Regex fallback for extracting size values.
    4. Keyword presence check.
    """
    response_text_clean = response_text.strip()
    
    # Try parsing as direct JSON
    try:
        data = json.loads(response_text_clean)
        if isinstance(data, dict) and "size" in data:
            return data.get("size").lower(), "Direct JSON"
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown blocks
    markdown_json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text_clean, re.DOTALL)
    if markdown_json_match:
        try:
            data = json.loads(markdown_json_match.group(1))
            if isinstance(data, dict) and "size" in data:
                return data.get("size").lower(), "Markdown JSON"
        except json.JSONDecodeError:
            pass

    # Try extracting via regex looking for 'size': '...' or "size": "..."
    regex_match = re.search(r"['\"]size['\"]\s*:\s*['\"](small|medium|large)['\"]", response_text_clean, re.IGNORECASE)
    if regex_match:
        return regex_match.group(1).lower(), "Regex Match"

    # Fallback to keyword presence check
    text_lower = response_text_clean.lower()
    if "large" in text_lower:
        return "large", "Keyword Match (large)"
    elif "medium" in text_lower:
        return "medium", "Keyword Match (medium)"
    elif "small" in text_lower:
        return "small", "Keyword Match (small)"

    return "unknown", "None (Fallback to default)"

def run_test(ollama_url, model_name):
    # Target folders
    non_dir = "data/Dữ_liệu_Nấm_non"
    mature_dir = "data/Dữ_liệu_Nấm_trưởng_thành"
    
    print("🔍 Selecting test images from dataset...")
    non_images = get_images_from_dir(non_dir, 2)
    mature_images = get_images_from_dir(mature_dir, 2)
    
    test_cases = []
    for img in non_images:
        test_cases.append({"path": img, "expected": "small"})
    for img in mature_images:
        test_cases.append({"path": img, "expected": "large"})
        
    if not test_cases:
        print("❌ No test images found in data folders. Please check your data paths.")
        return
        
    print(f"📋 Loaded {len(test_cases)} test cases:")
    for idx, case in enumerate(test_cases, 1):
        print(f"  {idx}. {case['path']} (Expected size: {case['expected']})")
    print(f"\n🚀 Starting tests against Ollama API: {ollama_url}")
    print(f"🤖 Model: {model_name}\n")
    
    results = []
    
    for idx, case in enumerate(test_cases, 1):
        img_path = case["path"]
        expected = case["expected"]
        
        print(f"[{idx}/{len(test_cases)}] Processing: {os.path.basename(img_path)}...")
        
        # Read and encode image to base64
        try:
            with open(img_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            results.append({
                "file": os.path.basename(img_path),
                "expected": expected,
                "detected": "ERROR",
                "method": "N/A",
                "latency": 0.0,
                "raw": f"Read error: {e}",
                "status": "FAIL"
            })
            continue

        payload = {
            "model": model_name,
            "prompt": "Describe the size of the orange mushroom growing out of the bag. Is it small or large?",
            "images": [img_base64],
            "stream": False
        }
        
        start_time = time.time()
        try:
            res = requests.post(ollama_url, json=payload, timeout=45)
            latency = time.time() - start_time
            
            if res.status_code == 200:
                raw_response = res.json().get("response", "").strip()
                detected, method = parse_llm_response(raw_response)
                
                # Compare detected to expected
                status = "PASS" if detected == expected else "FAIL"
                
                print(f"  ✅ Complete in {latency:.2f}s")
                print(f"  Raw response: {raw_response}")
                print(f"  Parsed size : {detected} (via {method})")
                print(f"  Result      : {status}")
                
                results.append({
                    "file": os.path.basename(img_path),
                    "expected": expected,
                    "detected": detected,
                    "method": method,
                    "latency": latency,
                    "raw": raw_response,
                    "status": status
                })
            else:
                print(f"  ❌ Ollama returned status code: {res.status_code}")
                results.append({
                    "file": os.path.basename(img_path),
                    "expected": expected,
                    "detected": "ERROR",
                    "method": "N/A",
                    "latency": latency,
                    "raw": f"HTTP {res.status_code}: {res.text}",
                    "status": "FAIL"
                })
        except requests.exceptions.RequestException as e:
            latency = time.time() - start_time
            print(f"  ❌ Failed to connect to Ollama: {e}")
            results.append({
                "file": os.path.basename(img_path),
                "expected": expected,
                "detected": "CONNECTION_ERROR",
                "method": "N/A",
                "latency": latency,
                "raw": str(e),
                "status": "FAIL"
            })

    # Print summary table
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"{'Image Name':<30} | {'Expected':<10} | {'Detected':<10} | {'Method':<20} | {'Time':<6} | {'Status'}")
    print("-"*80)
    
    passed_count = 0
    for r in results:
        status_symbol = "🟢 PASS" if r["status"] == "PASS" else "🔴 FAIL"
        if r["status"] == "PASS":
            passed_count += 1
        print(f"{r['file'][:30]:<30} | {r['expected']:<10} | {r['detected']:<10} | {r['method']:<20} | {r['latency']:5.2f}s | {status_symbol}")
    
    print("="*80)
    print(f"Success Rate: {passed_count}/{len(test_cases)} ({passed_count/len(test_cases)*100:.1f}%)")
    print("="*80)
    
    # Export results as JSON block
    print("\n" + "="*80)
    print("📋 JSON FORMATTED OUTPUT:")
    print("="*80)
    json_output = {
        "model": model_name,
        "success_rate": f"{passed_count}/{len(test_cases)}",
        "results": [
            {
                "file": r["file"],
                "expected": r["expected"],
                "detected": r["detected"],
                "status": r["status"],
                "latency_seconds": round(r["latency"], 2)
            } for r in results
        ]
    }
    print(json.dumps(json_output, indent=2, ensure_ascii=False))
    print("="*80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Ollama Vision model on mushroom images.")
    parser.add_argument("--url", default="http://localhost:11434/api/generate", 
                        help="Ollama API endpoint (default: http://localhost:11434/api/generate)")
    parser.add_argument("--model", default="moondream", 
                        help="Vision model name in Ollama (default: moondream)")
    
    args = parser.parse_args()
    run_test(args.url, args.model)
