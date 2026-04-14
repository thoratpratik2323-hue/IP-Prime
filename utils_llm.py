import os
import logging
import anthropic
from typing import Optional, List, Dict, Any

log = logging.getLogger("ipprime.llm")

# --- Environment Variables ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL_NAME = os.getenv("NVIDIA_MODEL_NAME", "meta/llama-3.1-405b-instruct")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1"

async def call_llm(
    client: Optional[anthropic.AsyncAnthropic] = None,
    system: Optional[str] = None,
    messages: List[Dict[str, str]] = None,
    model: str = "claude-3-5-sonnet-20251022",
    max_tokens: int = 256,
    temperature: float = 0.2
) -> str:
    """Universal LLM caller that supports Anthropic and NVIDIA NIM."""
    
    # 1. Try NVIDIA NIM if key is present (Priority)
    if NVIDIA_API_KEY:
        try:
            from openai import AsyncOpenAI
            nv_client = AsyncOpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_API_URL)
            
            # Convert system prompt to message for OpenAI format
            openai_messages = []
            if system:
                openai_messages.append({"role": "system", "content": system})
            
            for m in messages:
                openai_messages.append({"role": m["role"], "content": m["content"]})
            
            # Map common Claude models to NVIDIA equivalents if needed
            # For now, just use NVIDIA_MODEL_NAME
            
            response = await nv_client.chat.completions.create(
                model=NVIDIA_MODEL_NAME,
                messages=openai_messages,
                temperature=temperature,
                top_p=0.7,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            log.error(f"NVIDIA API Error: {e}")
            if not client:
                raise e

    # 2. Fallback to Anthropic Claude
    if not client and ANTHROPIC_API_KEY:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    
    if not client:
        raise ValueError("No LLM client or API keys available.")

    # Model mapping - ensure we use valid Anthropic models
    if "haiku" in model.lower():
        anthropic_model = "claude-3-5-haiku-20241022"
    elif "opus" in model.lower():
        anthropic_model = "claude-3-opus-20240229"
    else:
        anthropic_model = "claude-3-5-sonnet-20241022"

    try:
        response = await client.messages.create(
            model=anthropic_model,
            max_tokens=max_tokens,
            system=system or "",
            messages=messages,
            temperature=temperature
        )
        return response.content[0].text
    except Exception as e:
        log.error(f"Anthropic API Error: {e}")
        raise e
