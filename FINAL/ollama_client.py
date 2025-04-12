import requests
import json
import time

class OllamaClient:
    def __init__(self, model_name="mistral", base_url="http://localhost:11434"):
        """
        Initialize client for Ollama API
        
        Args:
            model_name: name of the model to use (default "mistral")
            base_url: URL of the Ollama API (default "http://localhost:11434")
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
        # Check if model is available
        self.is_available = self._check_model_available()
        
    def _check_model_available(self):
        """Check if the specified model is available in Ollama"""
        try:
            response = requests.get(f"{self.api_url}/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model.get("name") == self.model_name for model in models)
            return False
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False
    
    def generate_response(self, prompt, system=None, max_tokens=1024, temperature=0.7, stream=False):
        """
        Generate a response from the model
        
        Args:
            prompt: user prompt text
            system: optional system prompt
            max_tokens: maximum number of tokens to generate
            temperature: sampling temperature (higher = more creative)
            stream: whether to stream the response
            
        Returns:
            model's response text or generator if streaming
        """
        if not self.is_available:
            return "Error: Model not available. Please check if Ollama is running and the model is installed."
        
        url = f"{self.api_url}/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
            
        try:
            if not stream:
                # Non-streaming response
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    return f"Error: {response.status_code} - {response.text}"
            else:
                # Streaming response
                response = requests.post(url, json=payload, stream=True)
                
                if response.status_code == 200:
                    # Return generator for streaming
                    def response_generator():
                        for line in response.iter_lines():
                            if line:
                                chunk = json.loads(line)
                                yield chunk.get("response", "")
                                
                                # Break if done
                                if chunk.get("done", False):
                                    break
                                    
                    return response_generator()
                else:
                    return f"Error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            return f"Error generating response: {e}"
    
    def chat_completion(self, messages, max_tokens=1024, temperature=0.7, stream=False):
        """
        Generate a chat completion using the chat API
        
        Args:
            messages: list of message dicts with role and content
            max_tokens: maximum number of tokens to generate
            temperature: sampling temperature
            stream: whether to stream the response
            
        Returns:
            model's response or generator if streaming
        """
        if not self.is_available:
            return "Error: Model not available. Please check if Ollama is running and the model is installed."
        
        url = f"{self.api_url}/chat"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        try:
            if not stream:
                # Non-streaming response
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "")
                else:
                    return f"Error: {response.status_code} - {response.text}"
            else:
                # Streaming response
                response = requests.post(url, json=payload, stream=True)
                
                if response.status_code == 200:
                    # Return generator for streaming
                    def response_generator():
                        for line in response.iter_lines():
                            if line:
                                chunk = json.loads(line)
                                message = chunk.get("message", {})
                                yield message.get("content", "")
                                
                                # Break if done
                                if chunk.get("done", False):
                                    break
                                    
                    return response_generator()
                else:
                    return f"Error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            return f"Error generating chat completion: {e}"
    
    def process_rag_prompt(self, prompt_data, temperature=0.7, stream=False):
        """
        Process a RAG prompt (system + user prompt with context)
        
        Args:
            prompt_data: dict with system and user prompts
            temperature: sampling temperature
            stream: whether to stream the response
            
        Returns:
            model's response
        """
        system = prompt_data.get("system", "")
        user = prompt_data.get("user", "")
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
        
        return self.chat_completion(messages, temperature=temperature, stream=stream)

# Example usage
if __name__ == "__main__":
    client = OllamaClient(model_name="mistral")
    
    if client.is_available:
        print("Model is available. Testing generation...")
        
        # Simple generation test
        response = client.generate_response(
            "What is a mutual fund?",
            system="You are a helpful financial advisor."
        )
        
        print("Response:")
        print(response)
        
        # Test chat API
        chat_response = client.chat_completion([
            {"role": "system", "content": "You are a helpful financial advisor."},
            {"role": "user", "content": "What is a mutual fund?"}
        ])
        
        print("\nChat API Response:")
        print(chat_response)
    else:
        print("Model not available. Please check if Ollama is running and the model is installed.")
        print("You can install the model with: ollama pull mistral") 