#!/usr/bin/env python3
"""
OpenRouter API Client for Ki Wellness
Replaces local Ollama model with cloud-based AI models
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenRouterClient:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        # Use custom preset as primary model
        self.primary_model = "@preset/ki-wellness"
        
        # Cost-effective fallback models (max $0.20/M input, $0.80/M output)
        self.fallback_models = [
            'openai/gpt-4o-mini',        # ~$0.15/M input, $0.60/M output
            'anthropic/claude-3-haiku',   # ~$0.25/M input, $1.25/M output (slightly over but good quality)
            'meta-llama/llama-3.1-8b-instruct', # ~$0.20/M input, $0.80/M output
            'google/gemini-flash-1.5',   # ~$0.075/M input, $0.30/M output
            'mistralai/mistral-7b-instruct', # ~$0.14/M input, $0.42/M output
            'microsoft/phi-3-mini-128k-instruct' # ~$0.15/M input, $0.60/M output
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
        max_tokens: int = 500,
        track_usage: bool = True
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
        
        start_time = datetime.now()
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Add usage tracking information
                if track_usage and 'usage' in response_data:
                    response_data['_usage_tracking'] = {
                        'model': model,
                        'response_time_ms': int((datetime.now() - start_time).total_seconds() * 1000),
                        'timestamp': datetime.now().isoformat()
                    }
                
                return response_data
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
            # Try primary model first, then cost-effective fallbacks
            models_to_try = [self.primary_model]
            
            # Add cost-effective fallback models
            cost_effective_model = self.select_cost_effective_model()
            if cost_effective_model and cost_effective_model not in models_to_try:
                models_to_try.append(cost_effective_model)
            
            # Add other fallbacks as backup
            for fallback in self.fallback_models[:2]:  # Limit to 2 additional fallbacks
                if fallback not in models_to_try:
                    models_to_try.append(fallback)
        
        # Try each model until one works
        last_error = None
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
                last_error = str(e)
                print(f"❌ Failed with model {model_to_try}: {last_error}")
                continue
        
        # If all models failed
        raise Exception(f"All models failed. Last error: {last_error}")
    
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

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing information for a model"""
        try:
            model_info = self.get_model_info(model)
            if not model_info:
                # Return safe default values instead of infinity
                return {"input": 0.20, "output": 0.80, "model": model}
            
            pricing = model_info.get('pricing', {})
            input_price = pricing.get('input', 0.20)
            output_price = pricing.get('output', 0.80)
            
            # Ensure we don't return infinity values
            if input_price == float('inf') or input_price is None:
                input_price = 0.20
            if output_price == float('inf') or output_price is None:
                output_price = 0.80
            
            return {
                "input": input_price,
                "output": output_price,
                "model": model
            }
        except Exception as e:
            print(f"❌ Error getting pricing for {model}: {e}")
            # Return safe default values instead of infinity
            return {"input": 0.20, "output": 0.80, "model": model}

    def select_cost_effective_model(self, max_input_cost: float = 0.20, max_output_cost: float = 0.80) -> str:
        """Select the most cost-effective model within budget constraints"""
        try:
            # Get pricing for all fallback models
            model_prices = []
            for model in self.fallback_models:
                pricing = self.get_model_pricing(model)
                if pricing["input"] <= max_input_cost and pricing["output"] <= max_output_cost:
                    model_prices.append(pricing)
            
            if not model_prices:
                print(f"⚠️ No models found within budget constraints (input: ${max_input_cost}/M, output: ${max_output_cost}/M)")
                # Fall back to the most affordable option
                return self.fallback_models[0]
            
            # Sort by total cost (input + output) and select the most affordable
            model_prices.sort(key=lambda x: x["input"] + x["output"])
            selected_model = model_prices[0]["model"]
            
            print(f"💰 Selected cost-effective model: {selected_model}")
            print(f"   Input cost: ${model_prices[0]['input']:.3f}/M")
            print(f"   Output cost: ${model_prices[0]['output']:.3f}/M")
            
            return selected_model
            
        except Exception as e:
            print(f"❌ Error selecting cost-effective model: {e}")
            return self.fallback_models[0]

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
