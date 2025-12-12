"""
LLM Handler - Fallback handler using multiple LLM providers.
Supports: Groq (primary), OpenAI, Gemini (fallback).
Uses JSON mode to eliminate hallucinations and ensure consistent output.
"""
import os
import re
import json
import asyncio
from typing import Optional, Dict, Any
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class LLMHandler(BaseHandler):
    """
    Fallback handler using multiple LLM providers.
    Priority: Groq > OpenAI > Gemini
    """
    
    priority = 100  # Lowest priority - fallback
    
    def __init__(self):
        self.providers = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers in priority order."""
        
        # 1. Groq (Fastest, highest rate limits)
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            self.providers.append(('groq', groq_key))
            logger.info("✅ Groq API available (primary)")
        
        # 2. OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.providers.append(('openai', openai_key))
            logger.info("✅ OpenAI API available")
        
        # 3. Gemini (fallback)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            self.providers.append(('gemini', gemini_key))
            logger.info("✅ Gemini API available (fallback)")
        
        if not self.providers:
            logger.warning("⚠️ No LLM API keys found!")
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        return len(self.providers) > 0
    
    async def handle(self, context: TaskContext) -> str:
        if not self.providers:
            raise RuntimeError("No LLM providers available")
        
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(context)
        
        # Try each provider in order
        for provider_name, api_key in self.providers:
            try:
                logger.info(f"🤖 Trying {provider_name}...")
                
                if provider_name == 'groq':
                    response = await self._call_groq(api_key, system_prompt, user_prompt)
                elif provider_name == 'openai':
                    response = await self._call_openai(api_key, system_prompt, user_prompt)
                elif provider_name == 'gemini':
                    response = await self._call_gemini(api_key, system_prompt, user_prompt)
                else:
                    continue
                
                answer = self._extract_answer(response)
                if answer:
                    logger.info(f"✅ {provider_name} succeeded: {answer[:100]}...")
                    return answer
                    
            except Exception as e:
                logger.error(f"❌ {provider_name} failed: {e}")
                continue
        
        raise RuntimeError("All LLM providers failed")
    
    async def _call_groq(self, api_key: str, system_prompt: str, user_prompt: str) -> str:
        """Call Groq API (llama-3.3-70b)."""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code == 429:
                logger.warning("Groq rate limit, waiting 5s...")
                await asyncio.sleep(5)
                raise Exception("Rate limited")
            
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
    
    async def _call_openai(self, api_key: str, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API (gpt-4o-mini)."""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
            )
            
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
    
    async def _call_gemini(self, api_key: str, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API."""
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            )
        )
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = await asyncio.to_thread(
            lambda: model.generate_content(full_prompt)
        )
        return response.text
    
    def _create_system_prompt(self) -> str:
        """Create a strict system prompt for structured output."""
        return """You are a precise quiz-solving assistant. You MUST respond with ONLY valid JSON.

Your response format MUST be exactly:
{
    "answer": "YOUR_ANSWER_HERE",
    "reasoning": "Brief explanation"
}

Rules:
1. NEVER include any text outside the JSON
2. The "answer" field must contain ONLY the final answer value
3. If the answer is a number, use a number (not a string)
4. If the answer is a list, use a JSON array
5. Be concise and precise
6. If unsure, make your best educated guess"""
    
    def _create_user_prompt(self, context: TaskContext) -> str:
        """Create user prompt with task context."""
        return f"""Solve this quiz task and return ONLY JSON with your answer.

TASK URL: {context.current_url}

TASK INSTRUCTIONS:
{context.page_text[:3000]}

AVAILABLE FILES:
{', '.join(context.extract_all_file_urls()) or 'None mentioned'}

YOUR EMAIL (for personalized tasks): {context.email}

Return ONLY valid JSON with "answer" field."""
    
    def _extract_answer(self, response: str) -> Optional[str]:
        """Extract answer from LLM response."""
        try:
            data = json.loads(response)
            
            if isinstance(data, dict):
                if 'answer' in data:
                    answer = data['answer']
                    if isinstance(answer, (list, dict)):
                        return json.dumps(answer)
                    return str(answer)
                
                for key in ['result', 'output', 'value', 'response']:
                    if key in data:
                        val = data[key]
                        if isinstance(val, (list, dict)):
                            return json.dumps(val)
                        return str(val)
            
            if isinstance(data, (list, dict)):
                return json.dumps(data)
            return str(data)
            
        except json.JSONDecodeError:
            return self._extract_from_text(response)
    
    def _extract_from_text(self, text: str) -> Optional[str]:
        """Extract answer from plain text response."""
        json_match = re.search(r'\{[^{}]*"answer"[^{}]*\}', text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if 'answer' in data:
                    return str(data['answer'])
            except:
                pass
        
        answer_match = re.search(r'answer[:\s]+["\']?(.+?)["\']?(?:\n|$)', text, re.IGNORECASE)
        if answer_match:
            return answer_match.group(1).strip()
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            return lines[0]
        
        return None
