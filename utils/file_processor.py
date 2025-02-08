from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import os
import re
from config import PDFConfig
from .text_splitter import TextSplitter
from .exceptions import (
    FileProcessError,
    FileSizeError,
    FileTypeError,
    FileReadError,
    FileCorruptedError,
    TextExtractionError,
    TextProcessError,
    ChunkProcessError,
    MergeError,
    EncodingError
)

class BaseFileProcessor(ABC):
    """文件处理器基类"""
    
    def __init__(self):
        """初始化处理器"""
        # 创建文本分块器
        self.text_splitter = TextSplitter(
            chunk_size=PDFConfig.CHUNK_SIZE,
            overlap_size=PDFConfig.OVERLAP_SIZE
        )
        
        # 验证文件大小限制
        self.max_file_size = PDFConfig.MAX_FILE_SIZE
        
        # 编译正则表达式
        self._url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self._email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        self._space_pattern = re.compile(r'\s+')
    
    @abstractmethod
    def _extract_text_from_file(self, file) -> str:
        """从文件中提取文本"""
        pass
    
    def _validate_file(self, file) -> None:
        """验证文件"""
        try:
            # 检查文件是否可读
            if not hasattr(file, 'read'):
                raise FileReadError("文件对象不可读")
            
            # 检查文件大小
            try:
                file_size = len(file.read())
                file.seek(0)  # 重置文件指针
            except Exception as e:
                raise FileReadError(f"文件读取失败: {str(e)}")
            
            if file_size > self.max_file_size:
                raise FileSizeError(
                    f"文件大小超过限制: {file_size} > {self.max_file_size} bytes"
                )
            
            # 检查文件是否为空
            if file_size == 0:
                raise FileCorruptedError("文件为空")
                
        except FileProcessError:
            raise
        except Exception as e:
            raise FileProcessError(f"文件验证失败: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """清理和规范化文本"""
        if not text:
            return ""
            
        try:
            # 检查文本编码
            try:
                text.encode('utf-8').decode('utf-8')
            except UnicodeError:
                raise EncodingError("文本包含无效的Unicode字符")
            
            # Unicode标准化
            if PDFConfig.NORMALIZE_UNICODE:
                text = text.strip()
            
            # 移除多余空格
            if PDFConfig.REMOVE_EXTRA_SPACES:
                text = self._space_pattern.sub(' ', text)
            
            # 移除URL
            if PDFConfig.REMOVE_URLS:
                text = self._url_pattern.sub('', text)
            
            # 移除邮箱地址
            if PDFConfig.REMOVE_EMAILS:
                text = self._email_pattern.sub('', text)
            
            # 检查清理后的文本是否为空
            cleaned_text = text.strip()
            if not cleaned_text:
                raise TextProcessError("清理后的文本为空")
            
            return cleaned_text
            
        except FileProcessError:
            raise
        except Exception as e:
            raise TextProcessError(f"文本清理失败: {str(e)}")
    
    def extract_text(self, file) -> List[str]:
        """处理文件并返回文本块列表"""
        try:
            # 验证文件
            self._validate_file(file)
            
            # 提取文本
            text = self._extract_text_from_file(file)
            if not text:
                raise TextExtractionError("提取的文本为空")
            
            # 分割文本
            try:
                chunks = self.text_splitter.split_text(text)
            except Exception as e:
                raise ChunkProcessError(f"文本分块失败: {str(e)}")
            
            if not chunks:
                raise ChunkProcessError("分块结果为空")
            
            return chunks
            
        except FileProcessError:
            raise
        except Exception as e:
            raise TextExtractionError(f"文本提取失败: {str(e)}")
    
    def merge_text(self, chunks: List[str]) -> str:
        """合并文本块"""
        try:
            if not chunks:
                raise MergeError("没有要合并的文本块")
            
            merged_text = self.text_splitter.merge_chunks(chunks)
            if not merged_text:
                raise MergeError("合并后的文本为空")
            
            return merged_text
            
        except FileProcessError:
            raise
        except Exception as e:
            raise MergeError(f"文本合并失败: {str(e)}")
    
    @staticmethod
    def get_processor(filename: str) -> 'BaseFileProcessor':
        """根据文件类型获取对应的处理器"""
        try:
            if not filename:
                raise FileTypeError("文件名为空")
                
            ext = os.path.splitext(filename)[1].lower()
            
            if ext == '.pdf':
                from .pdf_processor import PDFProcessor
                return PDFProcessor()
            elif ext in ['.doc', '.docx']:
                from .word_processor import WordProcessor
                return WordProcessor()
            else:
                raise FileTypeError(f"不支持的文件类型: {ext}")
                
        except FileTypeError:
            raise
        except Exception as e:
            raise FileProcessError(f"处理器创建失败: {str(e)}")
    
    @staticmethod
    def get_supported_extensions() -> List[str]:
        """获取支持的文件扩展名列表"""
        return ['.pdf', '.doc', '.docx']