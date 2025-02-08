from typing import List, Tuple
import re
from config import PDFConfig

class TextSplitter:
    """文本分块处理器"""
    
    def __init__(
        self,
        chunk_size: int = PDFConfig.CHUNK_SIZE,
        overlap_size: int = PDFConfig.OVERLAP_SIZE
    ):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        
        # 编译正则表达式
        self.sentence_ends = r'[。！？!?]+'
        self.sentence_pattern = re.compile(f'([^{self.sentence_ends}]*[{self.sentence_ends}])')
    
    def split_text(self, text: str) -> List[str]:
        """将文本分割成块，保持上下文连贯性"""
        if not text:
            return []
            
        # 预处理文本，规范化换行和空格
        text = self._preprocess_text(text)
        
        # 按段落分割
        paragraphs = self._split_into_paragraphs(text)
        
        # 生成初始块
        chunks = self._create_chunks(paragraphs)
        
        # 处理重叠，确保上下文连贯
        if self.overlap_size > 0 and len(chunks) > 1:
            chunks = self._add_context_overlap(chunks)
        
        return chunks
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 规范化换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 规范化空格
        text = re.sub(r'\s+', ' ', text)
        # 确保段落之间有统一的分隔
        text = text.replace('\n\n', '<PARA>')
        text = text.replace('\n', ' ')
        text = text.replace('<PARA>', '\n\n')
        return text.strip()
    
    def _split_into_paragraphs(self, text: str) -> List[Tuple[str, bool]]:
        """将文本分割成段落，并标记是否是标题"""
        paragraphs = []
        current_title = None
        
        for para in text.split('\n\n'):
            para = para.strip()
            if not para:
                continue
                
            # 检查是否是标题（以#开头或者很短的段落）
            is_title = para.startswith('#') or (len(para) < 40 and not para[-1] in '。！？!?')
            
            # 如果是标题，保存当前标题
            if is_title:
                current_title = para
                paragraphs.append((para, True))
            else:
                # 如果有标题且不是第一个段落，添加标题上下文
                if current_title and paragraphs:
                    para = f"{current_title}\n{para}"
                paragraphs.append((para, False))
                
        return paragraphs
    
    def _create_chunks(self, paragraphs: List[Tuple[str, bool]]) -> List[str]:
        """创建初始文本块"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para, is_title in paragraphs:
            # 如果是标题，总是开始新的块
            if is_title and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [para]
                current_size = len(para)
                continue
            
            # 如果段落超过块大小限制
            if len(para) > self.chunk_size:
                # 先保存当前块
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # 分句处理长段落
                sentences = self._split_into_sentences(para)
                temp_chunk = []
                temp_size = 0
                
                for sent in sentences:
                    if temp_size + len(sent) <= self.chunk_size:
                        temp_chunk.append(sent)
                        temp_size += len(sent)
                    else:
                        if temp_chunk:
                            chunks.append(''.join(temp_chunk))
                        temp_chunk = [sent]
                        temp_size = len(sent)
                
                if temp_chunk:
                    chunks.append(''.join(temp_chunk))
            
            # 处理正常大小的段落
            elif current_size + len(para) <= self.chunk_size:
                current_chunk.append(para)
                current_size += len(para)
            else:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [para]
                current_size = len(para)
        
        # 添加最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        sentences = []
        last_end = 0
        
        for match in self.sentence_pattern.finditer(text):
            sentence = match.group(1)
            if sentence:
                sentences.append(sentence)
                last_end = match.end()
        
        # 处理剩余文本
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                sentences.append(remaining)
        
        return sentences
    
    def _add_context_overlap(self, chunks: List[str]) -> List[str]:
        """添加上下文重叠"""
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue
            
            # 获取上文
            prev_chunk = chunks[i-1]
            
            # 查找上一个块的最后一个完整句子
            prev_sentences = self._split_into_sentences(prev_chunk)
            context_sentences = []
            context_size = 0
            
            for sent in reversed(prev_sentences):
                if context_size + len(sent) > self.overlap_size:
                    break
                context_sentences.insert(0, sent)
                context_size += len(sent)
            
            # 添加上下文
            if context_sentences:
                context = ''.join(context_sentences)
                chunk = f"{context}\n\n{chunk}"
            
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def merge_chunks(self, chunks: List[str]) -> str:
        """合并文本块，去除重复内容"""
        if not chunks:
            return ""
            
        if len(chunks) == 1:
            return chunks[0]
            
        merged = chunks[0]
        for i in range(1, len(chunks)):
            current_chunk = chunks[i]
            # 查找重叠部分
            overlap = self._find_overlap(merged, current_chunk)
            if overlap:
                # 去除重叠部分，再拼接
                merged += current_chunk[len(overlap):]
            else:
                merged += '\n\n' + current_chunk
                
        return merged
    
    def _find_overlap(self, text1: str, text2: str) -> str:
        """查找两段文本之间的重叠部分"""
        min_overlap = 10  # 最小重叠长度
        max_overlap = self.overlap_size * 2  # 最大重叠长度
        
        # 获取text1的末尾和text2的开头
        end = text1[-max_overlap:] if len(text1) > max_overlap else text1
        start = text2[:max_overlap] if len(text2) > max_overlap else text2
        
        # 查找最长的重叠部分
        overlap = ""
        for i in range(len(end), min_overlap-1, -1):
            if end[-i:] == start[:i]:
                overlap = end[-i:]
                break
                
        return overlap