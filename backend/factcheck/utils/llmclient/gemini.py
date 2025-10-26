import time
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .base import BaseClient


class GeminiClient(BaseClient):
    """
    Gemini API client for fact verification.
    
    Compatible with Gemini 2.5 Flash and Pro models.
    Free tier available via Google AI Studio: https://aistudio.google.com/
    """
    
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_config: dict = None,
        max_requests_per_minute: int = 8,  # Free tier: 60 RPM for Flash, 15 for Pro
        request_window: int = 60,
    ):
        """
        Initialize the Gemini client.
        
        Args:
            model: Gemini model name (default: "gemini-2.5-flash")
                   Options: "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-8b"
            api_config: Configuration dict with GEMINI_API_KEY
            max_requests_per_minute: Rate limit (default: 60 for free tier)
            request_window: Time window in seconds for rate limiting
        """
        super().__init__(model, api_config, max_requests_per_minute, request_window)
        
        # Validate API key
        if "GEMINI_API_KEY" not in self.api_config:
            raise ValueError("GEMINI_API_KEY not found in api_config. Get one from https://aistudio.google.com/")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_config["GEMINI_API_KEY"])
        
        # Initialize the model with JSON mode
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 16000,
            "response_mime_type": "application/json",  # Ensures JSON output
        }
        
        self.client = genai.GenerativeModel(
            model_name=self.model,
            generation_config=generation_config,
        )

    def _call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Call Gemini API with the given messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional arguments (seed is accepted but not used by Gemini)
        
        Returns:
            JSON string response from Gemini
        """
        seed = kwargs.get("seed", 5)
        if not isinstance(seed, int):
            raise ValueError("Seed must be an integer.")
        
        # Note: Gemini doesn't support seed parameter directly
        # For reproducibility, consider using temperature=0
        
        # Convert OpenAI-style messages to Gemini format
        prompt = self._convert_messages_to_prompt(messages)
        
        try:
            # Generate content with Gemini
            response = self.client.generate_content(prompt)
            
            # Extract text from response
            if response.candidates:
                r = response.candidates[0].content.parts[0].text
            else:
                raise ValueError("No response candidates returned from Gemini")
            
            # Log usage if available
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                self._log_usage(usage_dict=response.usage_metadata)
            else:
                print("Warning: Gemini API usage metadata not available.")
            
            return r
            
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            raise

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to a single Gemini prompt.
        
        Gemini uses a simpler prompt format, so we combine system and user messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Combined prompt string
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System Instructions: {content}\n")
            elif role == "user":
                prompt_parts.append(f"{content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
        
        return "\n".join(prompt_parts)

    def _log_usage(self, usage_dict) -> None:
        """
        Log token usage from Gemini API response.
        
        Args:
            usage_dict: UsageMetadata object from Gemini response
        """
        try:
            # Gemini uses different field names
            if hasattr(usage_dict, "prompt_token_count"):
                self.usage.prompt_tokens += usage_dict.prompt_token_count
            if hasattr(usage_dict, "candidates_token_count"):
                self.usage.completion_tokens += usage_dict.candidates_token_count
        except Exception as e:
            print(f"Warning: Could not log usage - {str(e)}")

    def get_request_length(self, messages: List[Dict[str, str]]) -> int:
        """
        Get the length of the request for rate limiting purposes.
        
        Args:
            messages: List of message dicts
        
        Returns:
            Request length (currently returns 1 for simplicity)
        """
        # Could be enhanced to return actual token count
        # using genai.count_tokens() if needed
        return 1

    def construct_message_list(
        self,
        prompt_list: List[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ) -> List[List[Dict[str, str]]]:
        """
        Construct a list of message lists from prompts.
        
        Args:
            prompt_list: List of user prompts
            system_role: System role instruction (default: JSON output assistant)
        
        Returns:
            List of message lists in OpenAI format (for compatibility)
        """
        messages_list = []
        for prompt in prompt_list:
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt},
            ]
            messages_list.append(messages)
        return messages_list
