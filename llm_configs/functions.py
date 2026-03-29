import time
import asyncio
import logging
import json
import os
from functools import wraps

from google import genai
from google.genai import types

from pydantic import BaseModel

logger = logging.getLogger(__name__)

def measure_time(func):
    """
    Decorator to measure the execution time of both synchronous and asynchronous functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Function {func.__name__} completed - Duration: {duration:.2f}s")
            return {
                'function': func.__name__,
                'result': result,
                'time_seconds': duration
            }
        except Exception as e:
            logger.exception(f"Error executing function {func.__name__}: {e}")
            raise e
    
    @wraps(func)
    async def wrapper_async(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Function {func.__name__} completed - Duration: {duration:.2f}s")
            return {
                'function': func.__name__,
                'result': result,
                'time_seconds': duration
            }
        except Exception as e:
            logger.exception(f"Error executing function {func.__name__}: {e}")
            raise e

    return wrapper_async if asyncio.iscoroutinefunction(func) else wrapper

@measure_time
def generate_gemini_json(client, user_prompt, system_instruction, pydantic_schema, model="gemini-2.5-flash"):
    """
    Generates structured JSON output using Google Gemini.
    
    Args:
        client: Google Gemini client
        user_prompt: Content sent by the user
        system_instruction: System behavior instructions
        pydantic_schema: Pydantic class for validation
        model: Model name (default: gemini-2.0-flash)
        
    Returns:
        dict containing 'output' (parsed Pydantic object) and token usage metadata.
    """
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=pydantic_schema,
        ),
    )
    
    # Validation and parsing into a Pydantic object
    parsed_result = pydantic_schema.model_validate_json(response.text)
    
    results = {
        'output': parsed_result,
        'model': response.model_version
    }
    
    # Collecting token usage metadata
    usage = response.usage_metadata
    if usage:
        tokens_input = getattr(usage, 'prompt_token_count', 0) or 0
        tokens_reasoning = getattr(usage, 'thoughts_token_count', 0) or 0
        tokens_output = getattr(usage, 'candidates_token_count', 0) or 0
        tokens_total = getattr(usage, 'total_token_count', 0) or 0

        results.update({
            'tokens_input': tokens_input,
            'tokens_reasoning': tokens_reasoning,
            'tokens_output': tokens_output,
            'tokens_total': tokens_total
        })

        try:
            # Carregar custos do arquivo llm_pricing.json
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            pricing_file = os.path.join(base_dir, "llm_pricing", "llm_pricing.json")
            with open(pricing_file, "r", encoding="utf-8") as f:
                pricing_data = json.load(f)
            
            # Recuperar custo do modelo usado
            model_pricing = pricing_data.get("models", {}).get(model)
            if model_pricing:
                price_input_1m = model_pricing.get("input", 0.0)
                price_output_1m = model_pricing.get("output", 0.0)
                
                # Regra: tokens de raciocínio são contados como output
                # Somamos os de candidates_token_count (output real) com thoughts_token_count
                total_output_tokens = tokens_output + tokens_reasoning
                
                cost_input = (tokens_input / 1_000_000) * price_input_1m
                cost_output = (total_output_tokens / 1_000_000) * price_output_1m
                total_cost = cost_input + cost_output
                
                # Armazenando float bruto com todas as casas decimais sem arredondar
                results['cost_api_usd'] = total_cost
                
        except Exception as e:
            logger.warning(f"Erro ao calcular custo via llm_pricing.json: {e}")

    return results