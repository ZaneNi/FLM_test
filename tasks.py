import csv
import time
import subprocess
import json
from abc import ABC, abstractmethod
from datetime import datetime

class BaseTestTask(ABC):
    """
    Abstract base class for all testing tasks.
    Enforces a standard interface for running tests and saving results.
    """
    def __init__(self, client):
        self.client = client
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_flm_version(self) -> str:
        print("Checking flm version...")
        try:
            version_result = subprocess.run(["flm", "-v"], capture_output=True, text=True)
            flm_version = version_result.stdout.strip().replace(" ", "_").replace("/", "_")
        except Exception as e:
            print(f"Failed to get flm version: {e}")
            flm_version = "unknown_version"
        print(f"Using flm version: {flm_version}")
        return flm_version
    
    def get_csv_filename(self, task_name: str) -> str:
        return f"{task_name}_results_{self.get_flm_version()}_{self.timestamp}.csv"

    def fetch_all_models(self) -> json:
        print("Fetching available models...")
        result = subprocess.run(["flm", "list", "--json"], capture_output=True, text=True, check=True)
        models_json = json.loads(result.stdout)
        return models_json

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
    def run(self, max_completion_tokens=-1):
        print("\n=== Starting LLM Tests ===")

        csv_filename = self.get_csv_filename("llm")
        
        all_models = self.fetch_all_models()
        self.models = [m["model"] for m in all_models.get("models", []) if m["model"] not in ["whisper-v3:turbo", "embed-gemma:300m"]]
        print("Testing the following LLM models:")
        for i, model in enumerate(self.models, 1):
            print(f"  {i}. {model}")

        non_stream_prompts = ["Teach me Maxwell's equations.", "What is pi * pi?"]
        stream_prompts = ["What is the largest ocean on Earth?", "Write a quick haiku about coding."]

        server_process = self.start_flm_server(audio="0", embed="0")

        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Model", "Mode", "Input", "Reasoning Content", "Output Content"])

            for model_id in self.models:
                print(f"\n--- Testing LLM model: {model_id} ---")
                time.sleep(5) 
                # Non-Stream Mode
                for prompt in non_stream_prompts:
                    try:
                        response = self.client.chat.completions.create(
                            model=model_id,
                            messages=[{"role": "user", "content": prompt}],
                            stream=False,
                            max_completion_tokens=max_completion_tokens
                        )
                        message = response.choices[0].message
                        output_content = message.content or ""
                        reasoning_content = getattr(message, "reasoning_content", "N/A") or "N/A"
                        
                        writer.writerow([model_id, "Non-Stream", prompt, reasoning_content, output_content])
                        time.sleep(1)
                    except Exception as e:
                        writer.writerow([model_id, "Non-Stream", prompt, f"ERROR: {e}", "N/A"])

                # Stream Mode
                for prompt in stream_prompts:
                    try:
                        response = self.client.chat.completions.create(
                            model=model_id,
                            messages=[{"role": "user", "content": prompt}],
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

                        writer.writerow([model_id, "Stream", prompt, reasoning_content or "N/A", output_content])
                        time.sleep(1)
                    except Exception as e:
                        writer.writerow([model_id, "Stream", prompt, f"ERROR: {e}", "N/A"])
        print("\nShutting down flm server...")
        server_process.terminate()
        server_process.wait()
        print(f"LLM tests complete. Saved to {csv_filename}")


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
        self.test_image_path = "./test_files/image/test_image.jpeg"  # Ensure this image exists for testing

    def load_image_base64(self, image_path):
        import base64
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    def run(self, max_generation_tokens=-1):
        print("\n=== Starting Image Tests ===")
        
        csv_filename = self.get_csv_filename("image")
        
        all_models = self.fetch_all_models()
        self.models = [m["model"] for m in all_models.get("models", []) if m.get("vlm", False)] 
        print("Testing the following Image models:")
        for i, model in enumerate(self.models, 1):
            print(f"  {i}. {model}")

        prompt = "Describe the image in detail."

        server_process = self.start_flm_server(audio="0", embed="0")

        # TODO: Implement OpenAI Image API calls (e.g., image generations)
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Model", "Mode", "Input", "Reasoning Content", "Output Content"])
            for model_id in self.models:
                print(f"\n--- Testing VLMs: {model_id} ---")
                time.sleep(5) 
                try: 
                    response = self.client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {
                                "role": "user", 
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url", 
                                        "image_url": {"url": f"data:image/jpeg;base64,{self.load_image_base64(self.test_image_path)}"}
                                    }
                                ]
                            }
                        ]
                    )
                    message = response.choices[0].message
                    output_content = message.content or ""
                    reasoning_content = getattr(message, "reasoning_content", "N/A") or "N/A"
                    
                    writer.writerow([model_id, "Non-Stream", prompt, reasoning_content, output_content])
                    time.sleep(1)
                except Exception as e:
                    writer.writerow([model_id, "Non-Stream", prompt, f"ERROR: {e}", "N/A"])

        print("\nShutting down flm server...")
        server_process.terminate()
        server_process.wait()
        print(f"Image tests complete. Saved to {csv_filename}")