#!/usr/bin/env python3
"""
OpenRouter API Client for Ki Wellness
Replaces local Ollama model with cloud-based AI models
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenRouterClient:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.primary_model = os.getenv('MODEL', 'openai/gpt-4o-mini')  # Primary model from .env
        self.fallback_models = [
            'openai/gpt-4o-mini',      # Reliable fallback
            'anthropic/claude-3-haiku', # Alternative option
            'meta-llama/llama-3.1-8b-instruct'  # Another fallback
        ]
        self.site_url = os.getenv('SITE_URL', 'https://ki-wellness.herokuapp.com')
        self.site_name = os.getenv('SITE_NAME', 'Ki Wellness')
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Generate chat completion using OpenRouter API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (if None, uses primary model)
            temperature: Response randomness (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary containing the API response
        """
        if not model:
            model = self.primary_model
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate a response to a single prompt with fallback models
        
        Args:
            prompt: The user's prompt/question
            model: Model to use (if None, tries primary then fallbacks)
            temperature: Response randomness
            max_tokens: Maximum tokens in response
            
        Returns:
            The generated response text
        """
        messages = [{"role": "user", "content": prompt}]
        
        # Determine which models to try
        models_to_try = []
        if model:
            models_to_try.append(model)
        else:
            # Try primary model first, then fallbacks
            models_to_try = [self.primary_model] + self.fallback_models
        
        # Try each model until one works
        for model_to_try in models_to_try:
            try:
                print(f"🔄 Trying model: {model_to_try}")
                response = self.chat_completion(
                    messages=messages,
                    model=model_to_try,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Extract the response content
                if response.get('choices') and len(response['choices']) > 0:
                    print(f"✅ Success with model: {model_to_try}")
                    return response['choices'][0]['message']['content']
                else:
                    raise Exception("No response content in API response")
                    
            except Exception as e:
                print(f"❌ Failed with model {model_to_try}: {str(e)}")
                continue
        
        # If all models failed
        raise Exception(f"All models failed. Last error: {str(e)}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenRouter
        
        Returns:
            List of available models
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                raise Exception(f"Failed to fetch models: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Error fetching models: {str(e)}")
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model
        
        Args:
            model_id: The model identifier
            
        Returns:
            Model information dictionary or None if not found
        """
        try:
            models = self.get_available_models()
            for model in models:
                if model.get('id') == model_id:
                    return model
            return None
        except Exception:
            return None

# Global client instance
openrouter_client = None

def get_openrouter_client() -> OpenRouterClient:
    """Get or create the global OpenRouter client instance"""
    global openrouter_client
    if openrouter_client is None:
        openrouter_client = OpenRouterClient()
    return openrouter_client

def generate_ai_response(prompt: str, model: Optional[str] = None) -> str:
    """
    Convenience function to generate AI responses
    
    Args:
        prompt: The user's prompt
        model: Optional model to use
        
    Returns:
        The generated response
    """
    try:
        client = get_openrouter_client()
        return client.generate_response(prompt, model=model)
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"
