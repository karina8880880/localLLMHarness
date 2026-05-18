import requests

class LLM:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.model = "qwen3.5:9b"

    def generate(self, prompt):
        response = requests.post(self.url, json={
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        return response.json()["response"]
