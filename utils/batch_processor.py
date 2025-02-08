from typing import List, Dict, Callable, Any
import asyncio
import logging
from config import APIConfig

class BatchProcessor:
    """批量处理管理器"""
    
    def __init__(
        self,
        max_workers: int = APIConfig.MAX_CONCURRENT,
        progress_callback: Callable[[float, str], None] = None
    ):
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self.max_retries = APIConfig.MAX_RETRIES
        self.retry_delay = APIConfig.RETRY_DELAY
        
        # 初始化日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    async def process_batch(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        description: str = "处理中"
    ) -> List[Any]:
        """批量处理项目"""
        try:
            total_items = len(items)
            results = []
            
            # 创建信号量来限制并发
            semaphore = asyncio.Semaphore(self.max_workers)
            
            async def process_item_with_semaphore(item, index):
                async with semaphore:
                    for retry in range(self.max_retries):
                        try:
                            result = await process_func(item)
                            if self.progress_callback:
                                progress = (index + 1) / total_items
                                self.progress_callback(progress, description)
                            return result
                        except Exception as e:
                            if retry < self.max_retries - 1:
                                self.logger.warning(f"处理失败，正在重试 ({retry + 1}/{self.max_retries}): {str(e)}")
                                await asyncio.sleep(self.retry_delay)
                            else:
                                self.logger.error(f"处理项目失败: {str(e)}")
                                return None
            
            # 并行处理所有项目
            tasks = [
                process_item_with_semaphore(item, i)
                for i, item in enumerate(items)
            ]
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks)
            
            # 过滤掉None结果
            return [r for r in results if r is not None]
            
        except Exception as e:
            self.logger.error(f"批处理失败: {str(e)}")
            raise