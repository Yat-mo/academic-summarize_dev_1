from openai import AsyncOpenAI
from typing import List, Optional, Callable, Dict, Any
import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from config import APIConfig
from prompts import get_prompts

class AIHandler:
    """AI API处理器"""
    
    def __init__(self, api_key: str, api_base: str, provider: str = "openai"):
        """初始化API处理器"""
        if not api_key:
            raise ValueError("API密钥不能为空")
        
        self.provider = provider
        self.config = APIConfig.get_config(provider)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base or self.config["api_base"]
        )
        
        # 初始化缓存
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        self.cache_expiry = timedelta(days=7)  # 缓存7天过期
        self._init_cache()
        
        print(f"初始化AI处理器: {provider}")
    
    def _init_cache(self):
        """初始化缓存目录"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
                print(f"创建缓存目录: {self.cache_dir}")
        except Exception as e:
            print(f"创建缓存目录失败: {str(e)}")
    
    def _get_cache_path(self, prompt_hash: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{prompt_hash}.json")
    
    def _read_cache(self, prompt_hash: str) -> Optional[str]:
        """读取缓存"""
        try:
            cache_path = self._get_cache_path(prompt_hash)
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查缓存是否过期
            cache_time = datetime.fromtimestamp(cache_data['timestamp'])
            if datetime.now() - cache_time > self.cache_expiry:
                os.remove(cache_path)  # 删除过期缓存
                return None
            
            return cache_data['result']
            
        except Exception as e:
            print(f"读取缓存失败: {str(e)}")
            return None
    
    def _write_cache(self, prompt_hash: str, result: str):
        """写入缓存"""
        try:
            cache_path = self._get_cache_path(prompt_hash)
            cache_data = {
                'timestamp': time.time(),
                'result': result
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"写入缓存失败: {str(e)}")
    
    def _calculate_hash(self, prompt: str, **kwargs) -> str:
        """计算提示词和参数的哈希值"""
        # 将所有参数组合成一个字符串
        params_str = json.dumps(kwargs, sort_keys=True)
        content = f"{prompt}|{params_str}|{self.provider}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def process_text(self, text: str, prompt_template: str) -> str:
        """处理单个文本块"""
        try:
            if not text or not prompt_template:
                raise ValueError("文本或提示词模板不能为空")
            
            print(f"处理文本块: 长度={len(text)}")
            
            # 格式化提示词
            prompt = prompt_template.format(text=text)
            
            # 调用API
            result = await self.get_completion_with_cache(prompt)
            
            if not result:
                raise Exception("API返回结果为空")
            
            print(f"处理完成: 结果长度={len(result)}")
            return result
            
        except Exception as e:
            print(f"处理文本失败: {str(e)}")
            raise Exception(f"处理文本失败: {str(e)}")
    
    async def get_completion_with_cache(
        self, 
        prompt: str,
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """获取API响应（带缓存）"""
        try:
            # 计算缓存键
            cache_key = self._calculate_hash(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 尝试从缓存获取
            cached_result = self._read_cache(cache_key)
            if cached_result is not None:
                print("使用缓存结果")
                return cached_result
            
            # 调用API
            result = await self.get_completion(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 写入缓存
            self._write_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            raise
    
    async def get_completion(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """获取API响应"""
        try:
            print(f"调用API: provider={self.provider}")  # 添加日志
            
            # 确保max_tokens在有效范围内
            if self.provider == "deepseek":
                max_tokens = min(max_tokens or self.config["max_tokens"], 4096)
            else:
                max_tokens = max_tokens or self.config["max_tokens"]
            
            response = await self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature or self.config["temperature"]
            )
            
            result = response.choices[0].message.content
            print(f"API调用成功: 结果长度={len(result)}")  # 添加日志
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"API调用错误: {error_msg}")  # 添加日志
            
            if "insufficient_user_quota" in error_msg:
                raise Exception("API配额不足，请检查账户余额或联系服务提供商")
            elif "invalid_api_key" in error_msg:
                raise Exception("API密钥无效，请检查API Key是否正确")
            elif "model_not_found" in error_msg:
                raise Exception(f"模型 {self.config['model']} 不可用，请尝试其他模型")
            elif "Invalid max_tokens" in error_msg:
                raise Exception(f"Token数量超出限制，当前提供商最大支持 {self.config['max_tokens']} tokens")
            else:
                raise Exception(f"API调用失败: {error_msg}")

    async def summarize(
        self, 
        chunks: List[str],
        mode: str
    ) -> str:
        """优化的文本处理方法"""
        # 合并小块
        merged_chunks = []
        current_chunk = ""
        max_size = 3000 if self.provider == "deepseek" else 6000
        
        for chunk in chunks:
            if len(current_chunk) + len(chunk) < max_size:
                current_chunk += "\n\n" + chunk if current_chunk else chunk
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        chunks = merged_chunks  # 使用合并后的块
        
        prompts = get_prompts(mode)
        prompt_template = prompts["summary_prompt"]
        
        # 更新总块数
        total_chunks = len(chunks)
        processed = 0
        
        # 并行处理所有文本块
        async def process_chunk(chunk: str) -> str:
            nonlocal processed
            prompt = f"{prompt_template}\n\n文本内容:\n{chunk}"
            result = await self.get_completion_with_cache(prompt)
            processed += 1
            if self.progress_callback:
                self.progress_callback(processed / total_chunks)
            return result
        
        try:
            chunk_summaries = await asyncio.gather(
                *[process_chunk(chunk) for chunk in chunks]
            )
        except Exception as e:
            raise Exception(f"处理文本块失败: {str(e)}")
        
        # 如果只有一个块，直接返回
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]
            
        # 合并多个块的总结
        try:
            return await self.merge_summaries(chunk_summaries, prompts["merge_prompt"])
        except Exception as e:
            raise Exception(f"���并总结失败: {str(e)}")

    async def merge_summaries(
        self, 
        summaries: List[str],
        merge_prompt_template: str
    ) -> str:
        """优化的合并策略"""
        # 如果摘要数量少，直接合并
        if len(summaries) <= 2:
            combined_text = "\n\n".join(summaries)
            return await self._merge_batch(combined_text, merge_prompt_template)
        
        # 分批合并
        batch_size = 3
        while len(summaries) > 1:
            new_summaries = []
            for i in range(0, len(summaries), batch_size):
                batch = summaries[i:i + batch_size]
                if len(batch) == 1:
                    new_summaries.append(batch[0])
                else:
                    combined_text = "\n\n".join(batch)
                    merged = await self._merge_batch(combined_text, merge_prompt_template)
                    new_summaries.append(merged)
            summaries = new_summaries
        
        return summaries[0]

    async def _merge_batch(self, text: str, merge_prompt_template: str) -> str:
        """合并文本"""
        try:
            prompt = f"{merge_prompt_template}\n\n文本内容:\n{text}"
            return await self.get_completion_with_cache(
                prompt,
                max_tokens=min(4096, self.config["max_tokens"])
            )
        except Exception as e:
            raise Exception(f"合并文本失败: {str(e)}")