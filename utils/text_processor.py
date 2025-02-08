from typing import List, Dict
import chardet
from .file_processor import BaseFileProcessor

class TextProcessor(BaseFileProcessor):
    def __init__(self):
        super().__init__()
    
    def extract_text(self, file) -> List[str]:
        """从文本文件中提取文本"""
        try:
            # 检测文件编码
            raw_content = file.read()
            if isinstance(raw_content, str):
                text = raw_content
            else:
                encoding = chardet.detect(raw_content)['encoding'] or 'utf-8'
                text = raw_content.decode(encoding)
            
            # 分块处理
            return self._split_text(text)
            
        except Exception as e:
            raise Exception(f"处理文本文件时出错：{str(e)}")
    
    def get_metadata(self, file) -> Dict:
        """获取文本文件元数据"""
        try:
            import os
            stat = os.stat(file.name)
            return {
                "filename": file.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime
            }
        except Exception as e:
            return {"error": str(e)}