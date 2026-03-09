import csv
import time
import subprocess
import json
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from datetime import datetime

from openai import OpenAI

class BaseTestTask(ABC):
    """
    Abstract base class for all testing tasks.
    Enforces a standard interface for running tests and saving results.
    """
    def __init__(self, base_url, run_local=False):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_url = base_url
        self.run_local = run_local
        self.client = OpenAI(base_url=base_url, api_key="flm")
        self.version = self._get_flm_version()
        self.models = self._fetch_all_models()
        
    def get_csv_filename(self, task_name: str) -> str:
        return f"{task_name}_results_v{self.version}_{self.timestamp}.csv"

    def _get_flm_version(self) -> str:
        print("\nChecking flm version...")
        try:
            response = urllib.request.urlopen(f"{self.base_url}/version", timeout=5)
            version_data = json.loads(response.read().decode('utf-8'))
            flm_version = version_data.get("version", "unknown_version")
            print(f"Detected flm version: {flm_version}")
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
            print(f"Error fetching flm version: {e}")
            flm_version = "unknown_version"
        return flm_version
    
    def _fetch_all_models(self) -> list:
        print("\nFetching available models...")
        try:
            response = urllib.request.urlopen(f"{self.base_url}/models", timeout=5)
            models_json = json.loads(response.read().decode('utf-8'))
            model_list = models_json.get("data", [])
            model_id = [m["id"] for m in model_list]
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            print(f"Error fetching models: {e}")
            model_id = []
        return model_id

    def start_flm_server(self, audio, embed):
        """Starts the flm server as a subprocess."""
        print("Starting flm server...")
        server_process = subprocess.Popen(["flm", "serve", "-a", audio, "-e", embed])
        time.sleep(5) # Allow server to boot
        return server_process

    @abstractmethod
    def run(self, *args, **kwargs):
        """Must be implemented by all subclasses"""
        pass


class LLMTask(BaseTestTask):

    def __init__(self, base_url, run_local=False):
        super().__init__(base_url, run_local)
        self.csv_filename = self.get_csv_filename("llm")

    def run(self, max_completion_tokens=-1):
        prompt = "Teach me Maxwell's equations."
        followup_prompt = "Summarize the your answer."

        stream_prompt = "Tell me a joke and explain why it's funny." 
        stream_followup_prompt = "Summarize the joke and its explanation."
        
        with open(self.csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Model", "Mode", "Input", "Reasoning Content", "Output Content"])
            print("\n=== Starting LLM Tests ===")
            print(f"Models found: {len(self.models)}")
            for model_id in self.models:
            # for model_id in self.models[2:4]:  # Limit to first 2 models for testing purposes
                print(f"\n--- Testing LLM model: {model_id} ---")
                print(f"Testing non-stream mode...\n")
                messages = [
                    {"role": "user", "content": prompt}
                ]
                # first round
                try:
                    print(f"Prompt: {prompt}")
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        stream=False,
                        max_completion_tokens=max_completion_tokens
                    )
                    reasoning_content = getattr(response.choices[0].message, "reasoning_content", "N/A") or "N/A"
                    output_content = response.choices[0].message.content or ""
                    writer.writerow([model_id, "Non-Stream", prompt, reasoning_content, output_content])
                    print("Done.")
                    time.sleep(1)

                    messages.append({
                        "role": "assistant",
                        "content": output_content
                    })
                    messages.append({
                        "role": "user",
                        "content": followup_prompt
                    })                    
                except Exception as e:
                    print(f"Error occurred in first round, model: {model_id}: {e}")
                    writer.writerow([model_id, "Non-Stream", prompt, f"ERROR: {e}", "N/A"])
                
                # second round with previous messages
                try:
                    print(f"Follow-up Prompt: {followup_prompt}")
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        stream=False,
                        max_completion_tokens=max_completion_tokens
                    )

                    reasoning_content = getattr(
                        response.choices[0].message, "reasoning_content", "N/A"
                    ) or "N/A"
                    output_content = response.choices[0].message.content or ""
                    writer.writerow([model_id, "Non-Stream", followup_prompt, reasoning_content, output_content])
                    print("Done.")
                    time.sleep(1)
                except Exception as e:
                    print(f"Error occurred in second round, model: {model_id}: {e}")
                    writer.writerow([model_id, "Non-Stream", prompt, f"ERROR: {e}", "N/A"])

                # Stream Mode
                print(f"\nTesting stream mode...\n")
                messages = [
                    {"role": "user", "content": stream_prompt}
                ]
                # first round
                try:
                    print(f"Prompt: {stream_prompt}")
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        stream=True,
                        max_completion_tokens=max_completion_tokens
                    )
                    output_content, reasoning_content = "", ""
                    
                    for chunk in response:
                        if not chunk.choices: continue
                        delta = chunk.choices[0].delta
                        
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            reasoning_content += delta.reasoning_content
                        if delta.content:
                            output_content += delta.content
                    writer.writerow([model_id, "Stream", stream_prompt, reasoning_content or "N/A", output_content])
                    print("Done.")
                    time.sleep(1)

                    messages.append({
                        "role": "assistant",
                        "content": output_content
                    })
                    messages.append({
                        "role": "user",
                        "content": stream_followup_prompt
                    })                    
                except Exception as e:
                    print(f"Error occurred in first round, model: {model_id}: {e}")
                    writer.writerow([model_id, "Stream", stream_prompt, f"ERROR: {e}", "N/A"])
                # second round with previous messages
                try:
                    print(f"Follow-up Prompt: {stream_followup_prompt}")
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        stream=True,
                        max_completion_tokens=max_completion_tokens
                    )
                    output_content, reasoning_content = "", ""
                    
                    for chunk in response:
                        if not chunk.choices: continue
                        delta = chunk.choices[0].delta
                        
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            reasoning_content += delta.reasoning_content
                        if delta.content:
                            output_content += delta.content
                    writer.writerow([model_id, "Stream", stream_followup_prompt, reasoning_content or "N/A", output_content])
                    print("Done.")
                    time.sleep(1)
                except Exception as e:
                    print(f"Error occurred in second round, model: {model_id}: {e}")
                    writer.writerow([model_id, "Stream", stream_followup_prompt, f"ERROR: {e}", "N/A"])
                print(f"Finished testing model: {model_id}")
        print(f"\nLLM tests complete. Saved to {self.csv_filename}")


class EmbeddingTask(BaseTestTask):
    def run(self):
        print("\n=== Starting Embedding Tests ===")
        
        csv_filename = self.get_csv_filename("embedding")        
        
        all_models = self.fetch_all_models()
        self.models = [m["model"] for m in all_models.get("models", []) if m["model"] in ["embed-gemma:300m"]]
        print("Testing the following Embedding models:")
        for i, model in enumerate(self.models, 1):
            print(f"  {i}. {model}")

        server_process = self.start_flm_server(audio=0, embed=1)

        # TODO: Implement OpenAI Embeddings API calls
        # client.embeddings.create(input="text", model=model_id)

        print("\nShutting down flm server...")
        server_process.terminate()
        server_process.wait()
        print(f"Embedding tests complete. Saved to {csv_filename}")

class AudioTask(BaseTestTask):
    def run(self):
        print("\n=== Starting Audio Tests ===")
        
        csv_filename = self.get_csv_filename("audio")
        
        all_models = self.fetch_all_models()
        self.models = [m["model"] for m in all_models.get("models", []) if m["model"] in ["whisper-v3:turbo"]]
        print("Testing the following Audio models:")
        for i, model in enumerate(self.models, 1):
            print(f"  {i}. {model}")

        server_process = self.start_flm_server(audio=1, embed=0)

        # TODO: Implement OpenAI Audio API calls (e.g., transcriptions/speech)

        print("\nShutting down flm server...")
        server_process.terminate()
        server_process.wait()
        print(f"Audio tests complete. Saved to {csv_filename}")

class ImageTask(BaseTestTask):

    def __init__(self, client):
        super().__init__(client)
        self.test_image1_path = "./test_files/image/test_image1.jpeg" 
        self.test_image2_path = "./test_files/image/test_image2.jpg"
        self.csv_filename = self.get_csv_filename("image")
        self.vlm = ["gemma3:4b", "medgemma:4b", "medgemma1.5:4b", "qwen2.5vl-it:3b", "qwen3vl-it:4b", "translategemma:4b"]
        self.models = [m for m in self.models if m in self.vlm]

    def load_image_base64(self, image_path):
        import base64
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    def run(self, max_generation_tokens=-1):
        prompt = "Describe these two images in detail."
        followup_prompt = "Make a story that connects the two images together."

        with open(self.csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Model", "Input", "Reasoning Content", "Output Content"])
            print("\n=== Starting Image Tests ===")
            print(f"Models found: {len(self.models)}")
            for model_id in self.models:
                print(f"\n--- Testing VLMs: {model_id} ---")
                messages = [
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text", 
                                "text": prompt
                            },
                            {
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/jpeg;base64,{self.load_image_base64(self.test_image1_path)}"}
                            },
                            {
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/jpg;base64,{self.load_image_base64(self.test_image2_path)}"}
                            }
                        ]
                    }
                ]
                # first round
                try: 
                    print(f"Prompt: {prompt}")
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        stream=True,
                        max_completion_tokens=max_generation_tokens
                    )
                    
                    output_content, reasoning_content = "", ""
                    
                    for chunk in response:
                        if not chunk.choices: continue
                        delta = chunk.choices[0].delta
                        
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            reasoning_content += delta.reasoning_content
                        if delta.content:
                            output_content += delta.content
                    writer.writerow([model_id, prompt, reasoning_content or "N/A", output_content])
                    print("Done.")
                    time.sleep(1)

                    messages.append({
                        "role": "assistant",
                        "content": output_content
                    })
                    messages.append({
                        "role": "user",
                        "content": followup_prompt
                    })                  
                except Exception as e:
                    print(f"Error occurred in first round, model: {model_id}: {e}")
                    writer.writerow([model_id, prompt, f"ERROR: {e}", "N/A"])
                
                
                # second round with previous messages
                try:
                    print(f"Follow-up Prompt: {followup_prompt}")
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        stream=True,
                        max_completion_tokens=max_generation_tokens
                    )
                    output_content, reasoning_content = "", ""
                    
                    for chunk in response:
                        if not chunk.choices: continue
                        delta = chunk.choices[0].delta
                        
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            reasoning_content += delta.reasoning_content
                        if delta.content:
                            output_content += delta.content
                    writer.writerow([model_id, followup_prompt, reasoning_content or "N/A", output_content])
                    print("Done.")
                    time.sleep(1)
                except Exception as e:
                    print(f"Error occurred in second round, model: {model_id}: {e}")
                    writer.writerow([model_id, followup_prompt, f"ERROR: {e}", "N/A"])
                print(f"Finished testing model: {model_id}")
        print(f"Image tests complete. Saved to {self.csv_filename}")