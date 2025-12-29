"""
LLM Client Wrapper
Supports async calls, retry mechanism, deep thinking models and robust JSON parsing

Features:
- Support for deep thinking models (auto-filter thinking process, only return final answer)
- Support for high token limits (for complex mathematical proofs)
- Robust JSON parsing (handle truncation and other issues)
"""

import asyncio
import json
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
import httpx
from config import (
    API_KEY, BASE_URL, MODEL,
    LLM_TIMEOUT, LLM_MAX_RETRIES, 
    LLM_DEFAULT_MAX_TOKENS, LLM_DEFAULT_TEMPERATURE
)

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM API Client - Supports deep thinking models"""
    
    def __init__(
        self,
        api_key: str = API_KEY,
        base_url: str = BASE_URL,
        model: str = MODEL,
        max_retries: int = LLM_MAX_RETRIES,
        timeout: float = LLM_TIMEOUT,
        default_max_tokens: int = LLM_DEFAULT_MAX_TOKENS
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.default_max_tokens = default_max_tokens
        
        # Detect if it's a deep thinking model
        self._is_thinking_model = self._detect_thinking_model(model)
        
    def _detect_thinking_model(self, model: str) -> bool:
        """Detect if it's a deep thinking model"""
        thinking_keywords = [
            'thinking', 'reason', 'o1', 'o3', 'deepthink', 
            'cot', 'chain-of-thought', 'reasoning'
        ]
        model_lower = model.lower()
        return any(kw in model_lower for kw in thinking_keywords)
    
    def _extract_final_answer(self, response_data: Dict[str, Any]) -> str:
        """
        Extract final answer from API response, filter out thinking process
        
        Supports multiple API formats:
        1. OpenAI format (including compatible APIs)
        2. Gemini format
        3. Claude format
        """
        # Get choices
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("No choices field in API response")
        
        message = choices[0].get("message", {})
        
        # Method 1: Standard content field
        content = message.get("content", "")
        
        # Method 2: Check if there's reasoning_content (some APIs separate thinking and answer)
        reasoning_content = message.get("reasoning_content")
        if reasoning_content is not None:
            # If there's separate reasoning_content, content is the final answer
            return content if content else ""
        
        # Method 3: Check if there's thinking field (Claude extended thinking format)
        thinking = message.get("thinking")
        if thinking is not None:
            # thinking is thinking process, content is final answer
            return content if content else ""
        
        # Method 4: Check if content is array format (some APIs' multimodal response)
        if isinstance(content, list):
            # Filter out text type content, exclude thinking type
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type", "text")
                    if item_type == "text":
                        text_parts.append(item.get("text", ""))
                    elif item_type in ["thinking", "reasoning"]:
                        # Skip thinking content
                        continue
                elif isinstance(item, str):
                    text_parts.append(item)
            return "\n".join(text_parts)
        
        # Method 5: If content is string, check if it contains thinking markers
        if isinstance(content, str) and self._is_thinking_model:
            content = self._remove_thinking_markers(content)
        
        return content if content else ""
    
    def _remove_thinking_markers(self, text: str) -> str:
        """
        Remove thinking markers from text
        
        Supported marker formats:
        - <thinking>...</thinking>
        - <thought>...</thought>
        - <reasoning>...</reasoning>
        - [Thinking]...[/Thinking]
        - 【Thinking】...【/Thinking】
        """
        if not text:
            return text
        
        # Define patterns to remove
        patterns = [
            r'<thinking>[\s\S]*?</thinking>',
            r'<thought>[\s\S]*?</thought>',
            r'<reasoning>[\s\S]*?</reasoning>',
            r'<think>[\s\S]*?</think>',
            r'\[思考\][\s\S]*?\[/思考\]',
            r'【思考】[\s\S]*?【/思考】',
            r'\[thinking\][\s\S]*?\[/thinking\]',
            r'\[THINKING\][\s\S]*?\[/THINKING\]',
        ]
        
        result = text
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        # Clean up excess whitespace
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
        
    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Send request to LLM API"""
        if max_tokens is None:
            max_tokens = self.default_max_tokens
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"[LLM] Sending request to {self.base_url}/chat/completions (model: {self.model})")
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # Use smart extraction to filter thinking content
                    content = self._extract_final_answer(result)
                    logger.info(f"[LLM] Response received, length: {len(content)} chars")
                    return content
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"[LLM] HTTP error (attempt {attempt+1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise Exception(f"API request failed: {e}")
                    await asyncio.sleep(2 ** attempt)
                except httpx.TimeoutException as e:
                    logger.error(f"[LLM] Timeout (attempt {attempt+1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise Exception(f"API request timeout: {e}")
                    await asyncio.sleep(2 ** attempt)
                except Exception as e:
                    logger.error(f"[LLM] Exception (attempt {attempt+1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Request exception: {e}")
                    await asyncio.sleep(2 ** attempt)
        
        raise Exception("API request failed, max retries reached")
    
    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Single turn conversation"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return await self._make_request(messages, temperature, max_tokens)
    
    async def chat_with_json_output(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.5,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Chat and parse JSON output, with retry"""
        last_error = None
        
        for attempt in range(2):  # Retry once if JSON parsing fails
            try:
                response = await self.chat(system_prompt, user_message, temperature, max_tokens)
                return self.extract_json(response)
            except ValueError as e:
                last_error = e
                if attempt == 0:
                    print(f"[LLM] JSON parsing failed, retrying...")
                    # Add stronger JSON format requirement
                    user_message = user_message + "\n\n【IMPORTANT REMINDER】Please ensure you output complete, properly formatted JSON, do not truncate."
        
        # If both fail, try lenient parsing
        try:
            return self.extract_json_lenient(response)
        except:
            raise last_error
    
    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """Extract JSON from text (strict mode)"""
        if not text:
            raise ValueError("Response is empty")
        
        # Preprocess: remove common non-JSON prefixes
        text = text.strip()
        
        # 1. Try to parse the entire text directly
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 2. Try to extract from ```json code block
        json_block_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_block_pattern, text)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                # Try to fix truncated JSON
                fixed = LLMClient._try_fix_truncated_json(match.strip())
                try:
                    return json.loads(fixed)
                except:
                    continue
        
        # 3. Try to extract from ``` code block
        code_block_pattern = r'```\s*([\s\S]*?)\s*```'
        matches = re.findall(code_block_pattern, text)
        for match in matches:
            cleaned = match.strip()
            if cleaned.startswith('{') or cleaned.startswith('['):
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    fixed = LLMClient._try_fix_truncated_json(cleaned)
                    try:
                        return json.loads(fixed)
                    except:
                        continue
        
        # 4. Try to find the outermost JSON object
        try:
            start = text.find('{')
            if start != -1:
                # Find matching closing brace
                depth = 0
                in_string = False
                escape_next = False
                end = -1
                
                for i in range(start, len(text)):
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                end = i + 1
                                break
                
                if end != -1:
                    json_str = text[start:end]
                    return json.loads(json_str)
                else:
                    # If no matching } found, try to fix
                    json_str = text[start:]
                    fixed = LLMClient._try_fix_truncated_json(json_str)
                    return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        raise ValueError(f"Unable to extract valid JSON from response:\n{text[:500]}...")
    
    @staticmethod
    def extract_json_lenient(text: str) -> Dict[str, Any]:
        """Lenient mode JSON parsing (try to fix common issues)"""
        if not text:
            raise ValueError("Response is empty")
        
        # Find JSON part
        start = text.find('{')
        if start == -1:
            raise ValueError("JSON object not found")
        
        # Extract from start position
        json_text = text[start:]
        
        # Try to fix truncated JSON
        json_text = LLMClient._try_fix_truncated_json(json_text)
        
        # Try to parse
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Try more aggressive fix
            json_text = LLMClient._aggressive_json_fix(json_text)
            try:
                return json.loads(json_text)
            except:
                raise ValueError(f"JSON parsing failed: {e}")
    
    @staticmethod
    def _try_fix_truncated_json(text: str) -> str:
        """Try to fix truncated JSON"""
        if not text:
            return "{}"
        
        result = text.rstrip()
        
        # Remove incomplete key-value pairs (incomplete parts after comma)
        # e.g.: {"a": 1, "b": 2, "c":  -> {"a": 1, "b": 2}
        lines = result.split('\n')
        valid_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip obviously incomplete lines
            if stripped.endswith(':') or stripped.endswith(': '):
                continue
            if '...' in stripped and '"' not in stripped:
                continue
            valid_lines.append(line)
        result = '\n'.join(valid_lines).rstrip()
        
        # If last character is comma or colon, remove it
        while result and result[-1] in ',:\n\t ':
            result = result[:-1]
        
        # If truncated in middle of string, try to close string
        quote_count = 0
        in_escape = False
        for c in result:
            if in_escape:
                in_escape = False
                continue
            if c == '\\':
                in_escape = True
                continue
            if c == '"':
                quote_count += 1
        
        if quote_count % 2 == 1:
            result += '"'
        
        # Calculate bracket balance
        open_braces = 0
        open_brackets = 0
        in_string = False
        escape_next = False
        
        for c in result:
            if escape_next:
                escape_next = False
                continue
            if c == '\\':
                escape_next = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if not in_string:
                if c == '{':
                    open_braces += 1
                elif c == '}':
                    open_braces -= 1
                elif c == '[':
                    open_brackets += 1
                elif c == ']':
                    open_brackets -= 1
        
        # Add missing brackets
        for _ in range(open_brackets):
            result += ']'
        
        # Add missing braces
        for _ in range(open_braces):
            result += '}'
        
        return result
    
    @staticmethod
    def _aggressive_json_fix(text: str) -> str:
        """More aggressive JSON fix"""
        # Remove potential trailing content
        lines = text.split('\n')
        valid_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip lines that are obviously not JSON
            if stripped.startswith('//') or stripped.startswith('#'):
                continue
            if '...' in stripped and not '"' in stripped:
                continue
            valid_lines.append(line)
        
        text = '\n'.join(valid_lines)
        
        # Try to fix again
        return LLMClient._try_fix_truncated_json(text)
    
    @staticmethod
    def extract_json_or_default(text: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Try to extract JSON, return default on failure"""
        try:
            return LLMClient.extract_json(text)
        except ValueError:
            try:
                return LLMClient.extract_json_lenient(text)
            except:
                return default


# Global client instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def reset_llm_client():
    """Reset global client"""
    global _client
    _client = None


async def call_llm(
    system_prompt: str,
    user_message: str,
    expect_json: bool = False,
    temperature: float = LLM_DEFAULT_TEMPERATURE,
    max_tokens: Optional[int] = None
) -> Any:
    """Convenience function: call LLM"""
    client = get_llm_client()
    if expect_json:
        return await client.chat_with_json_output(
            system_prompt, user_message, temperature, max_tokens
        )
    else:
        return await client.chat(
            system_prompt, user_message, temperature, max_tokens
        )


async def call_llm_safe(
    system_prompt: str,
    user_message: str,
    default: Dict[str, Any] = None,
    temperature: float = LLM_DEFAULT_TEMPERATURE,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """Safe LLM call, return default on failure"""
    if default is None:
        default = {}
    
    client = get_llm_client()
    try:
        response = await client.chat(system_prompt, user_message, temperature, max_tokens)
        return client.extract_json_or_default(response, default)
    except Exception as e:
        print(f"[LLM] Call failed: {e}")
        return default
