from openai import AsyncOpenAI
import asyncio
from typing import List, Dict, Any
import prompts
import config
from prompts import get_prompt
from prompts_popular import POPULAR_PROMPT

class OpenAIHandler:
    _api_key = None
    _api_base = None
    
    def __init__(self, api_key: str, api_base: str = None):
        OpenAIHandler._api_key = api_key
        OpenAIHandler._api_base = api_base
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base if api_base else "https://api.openai.com/v1"
        )
    
    @classmethod
    def get_api_key(cls) -> str:
        return cls._api_key
    
    @classmethod
    def get_api_base(cls) -> str:
        return cls._api_base
        
    async def summarize_chunk(self, chunk: str, mode: str, style: str = "学术模式") -> str:
        try:
            if style == "学术模式":
                prompt = get_prompt(mode)
            else:
                prompt = POPULAR_PROMPT
                
            response = await self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": chunk}
                ],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error processing chunk: {str(e)}")
            return ""

    async def summarize(self, chunks: List[str], mode: str, style: str = "学术模式") -> str:
        tasks = [self.summarize_chunk(chunk, mode, style) for chunk in chunks]
        chunk_summaries = await asyncio.gather(*tasks)
        
        # 合并各个部分的总结
        merged_summary = await self.merge_summaries(chunk_summaries, mode)
        return merged_summary
    
    async def merge_summaries(self, summaries: List[str], mode: str) -> str:
        merged_text = "\n\n".join(summaries)
        
        response = await self.client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": prompts.MERGE_PROMPT},
                {"role": "user", "content": merged_text}
            ],
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS
        )
        
        return response.choices[0].message.content 