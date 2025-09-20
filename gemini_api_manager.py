#!/usr/bin/env python3
"""
Enhanced Gemini API Manager with Robust Request Handling
Addresses quota exhaustion issues with intelligent rate limiting and retry logic
"""

import asyncio
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# New Gemini API
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    # Fallback for older API structure
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Warning: Google Generative AI library not properly installed")
        genai = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIKeyConfig:
    """Configuration for API key with usage tracking"""
    key: str
    daily_limit: int = 50  # Free tier limit
    current_usage: int = 0
    last_reset: datetime = None
    is_disabled: bool = False
    backoff_until: Optional[datetime] = None

class GeminiAPIManager:
    """
    Enhanced Gemini API manager with:
    - Multiple API key rotation
    - Intelligent rate limiting
    - Usage tracking and quota management
    - Exponential backoff for rate limits
    - Request queuing and batching
    """
    
    def __init__(self, api_keys: List[str]):
        self.api_configs = [
            APIKeyConfig(key=key, last_reset=datetime.now()) 
            for key in api_keys
        ]
        self.current_key_index = 0
        self.clients = {}
        self.request_queue = asyncio.Queue()
        self.is_processing = False
        
        # Rate limiting configuration
        self.min_request_interval = 2.0  # seconds between requests
        self.max_retries = 3
        self.base_backoff = 5.0  # seconds
        self.max_backoff = 300.0  # 5 minutes max backoff
        
        self._setup_clients()
    
    def _setup_clients(self):
        """Initialize Gemini clients for all API keys"""
        if genai is None:
            logger.error("❌ Google Generative AI library not available")
            return
            
        for i, config in enumerate(self.api_configs):
            try:
                # Configure the API key for this client
                genai.configure(api_key=config.key)
                self.clients[config.key] = genai  # Store reference to configured genai
                logger.info(f"✅ Initialized Gemini client {i+1}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize client {i+1}: {e}")
                config.is_disabled = True
    
    def _reset_daily_usage_if_needed(self, config: APIKeyConfig):
        """Reset usage counter if a day has passed"""
        if config.last_reset and datetime.now() - config.last_reset >= timedelta(days=1):
            config.current_usage = 0
            config.last_reset = datetime.now()
            config.is_disabled = False
            logger.info(f"🔄 Reset daily usage for API key ending in ...{config.key[-4:]}")
    
    def _get_available_key(self) -> Optional[APIKeyConfig]:
        """Get next available API key with quota"""
        for _ in range(len(self.api_configs)):
            config = self.api_configs[self.current_key_index]
            self._reset_daily_usage_if_needed(config)
            
            # Check if key is available
            if not config.is_disabled and config.current_usage < config.daily_limit:
                if config.backoff_until is None or datetime.now() > config.backoff_until:
                    return config
            
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_configs)
        
        return None
    
    def _handle_rate_limit_error(self, config: APIKeyConfig, error_msg: str):
        """Handle rate limit errors with intelligent backoff"""
        if "quota" in error_msg.lower() or "daily" in error_msg.lower():
            # Daily quota exceeded
            config.is_disabled = True
            logger.warning(f"📊 Daily quota exceeded for key ...{config.key[-4:]}")
        else:
            # Temporary rate limit - apply backoff
            backoff_time = min(self.max_backoff, self.base_backoff * (2 ** config.current_usage))
            config.backoff_until = datetime.now() + timedelta(seconds=backoff_time)
            logger.warning(f"⏸️ Rate limited key ...{config.key[-4:]}, backing off for {backoff_time:.1f}s")
    
    async def generate_content_safe(self, 
                                   prompt: str, 
                                   model: str = "gemini-2.0-flash-exp",
                                   max_retries: int = 3) -> Optional[str]:
        """
        Generate content with comprehensive error handling and retry logic
        
        Args:
            prompt: The prompt to send to Gemini
            model: Model name to use
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated content or None if all attempts failed
        """
        
        for attempt in range(max_retries):
            # Get available API key
            config = self._get_available_key()
            if not config:
                wait_time = 60  # Wait 1 minute before checking again
                logger.warning(f"🚫 No available API keys. Waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            
            client = self.clients.get(config.key)
            if not client:
                continue
            
            try:
                # Add delay between requests to avoid rate limiting
                await asyncio.sleep(self.min_request_interval)
                
                logger.info(f"🚀 Attempting request with key ...{config.key[-4:]} (usage: {config.current_usage}/{config.daily_limit})")
                
                # Configure API key for this request
                genai.configure(api_key=config.key)
                
                # Create model and generate content
                model_instance = genai.GenerativeModel(model)
                generation_config = genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                    top_p=0.9,
                    top_k=40
                )
                
                response = model_instance.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Success - update usage and return result
                config.current_usage += 1
                logger.info(f"✅ Request successful. Usage: {config.current_usage}/{config.daily_limit}")
                
                return response.text
                
            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"⚠️ API Error (attempt {attempt+1}): {str(e)[:150]}...")
                
                # Handle different types of errors
                if "quota" in error_msg or "rate" in error_msg or "exceeded" in error_msg:
                    self._handle_rate_limit_error(config, error_msg)
                elif "invalid" in error_msg or "authentication" in error_msg:
                    config.is_disabled = True
                    logger.error(f"🔑 Invalid API key ...{config.key[-4:]}, disabling")
                else:
                    # Generic error - apply exponential backoff
                    backoff_time = min(self.max_backoff, self.base_backoff * (2 ** attempt))
                    logger.warning(f"💤 Retrying after {backoff_time:.1f}s...")
                    await asyncio.sleep(backoff_time)
        
        logger.error("❌ All retry attempts exhausted")
        return None
    
    async def batch_generate(self, prompts: List[str], delay_between_requests: float = 3.0) -> List[Optional[str]]:
        """
        Generate content for multiple prompts with intelligent pacing
        
        Args:
            prompts: List of prompts to process
            delay_between_requests: Minimum delay between requests in seconds
            
        Returns:
            List of generated content (None for failed requests)
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"📝 Processing prompt {i+1}/{len(prompts)}")
            
            result = await self.generate_content_safe(prompt)
            results.append(result)
            
            # Add delay between requests (except for the last one)
            if i < len(prompts) - 1:
                logger.info(f"⏱️ Waiting {delay_between_requests}s before next request...")
                await asyncio.sleep(delay_between_requests)
        
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        stats = {
            "total_keys": len(self.api_configs),
            "active_keys": sum(1 for c in self.api_configs if not c.is_disabled),
            "keys": []
        }
        
        for i, config in enumerate(self.api_configs):
            key_stats = {
                "key_id": f"key_{i+1}_...{config.key[-4:]}",
                "usage": f"{config.current_usage}/{config.daily_limit}",
                "usage_percentage": (config.current_usage / config.daily_limit) * 100,
                "is_disabled": config.is_disabled,
                "backoff_until": config.backoff_until.isoformat() if config.backoff_until else None
            }
            stats["keys"].append(key_stats)
        
        return stats
    
    def print_usage_report(self):
        """Print a formatted usage report"""
        stats = self.get_usage_stats()
        
        print("\n" + "="*60)
        print("🤖 GEMINI API USAGE REPORT")
        print("="*60)
        print(f"📊 Total API Keys: {stats['total_keys']}")
        print(f"✅ Active Keys: {stats['active_keys']}")
        print("-"*60)
        
        for key_stat in stats["keys"]:
            status = "🟢" if not key_stat["is_disabled"] else "🔴"
            print(f"{status} {key_stat['key_id']}: {key_stat['usage']} ({key_stat['usage_percentage']:.1f}%)")
            if key_stat["backoff_until"]:
                print(f"    ⏸️ Backed off until: {key_stat['backoff_until']}")
        
        print("="*60)

# Example usage and testing
async def test_api_manager():
    """Test the API manager with sample prompts"""
    
    # Your API keys
    api_keys = [
        "AIzaSyC7lW99lDFrBFS3e5mYxZNJzIn4tyFNFE",
        "AIzaSyAq7dfXdFagW2j2AdbfgCkj8s6nahUMjOg", 
        "AIzaSyA5SqoM2v_9VFG2O6DbxBGKftm3onsHGpM",
        "AIzaSyAuiUoHva-1iZFJh2C4asr9pTL7gQLNci4"
    ]
    
    manager = GeminiAPIManager(api_keys)
    
    # Test prompts
    test_prompts = [
        "What is cognitive load theory in simple terms?",
        "Explain stress detection in educational systems.",
        "What are the key principles of adaptive learning?"
    ]
    
    print("🚀 Starting API Manager Test...")
    manager.print_usage_report()
    
    # Test single request
    result = await manager.generate_content_safe("Hello, please respond with a simple greeting.")
    print(f"📝 Single request result: {result[:100] if result else 'Failed'}")
    
    # Test batch processing
    results = await manager.batch_generate(test_prompts, delay_between_requests=5.0)
    print(f"📦 Batch results: {len([r for r in results if r])} successful out of {len(results)}")
    
    # Final usage report
    manager.print_usage_report()

if __name__ == "__main__":
    asyncio.run(test_api_manager())