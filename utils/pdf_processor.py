import pdfplumber
import config
from typing import List, Generator
import streamlit as st

class PDFProcessor:
    def __init__(self, file=None):
        self.file = file
        
    def extract_text(self, file) -> List[str]:
        """从PDF文件中提取文本内容"""
        self.file = file
        chunks = []
        
        try:
            with pdfplumber.open(self.file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    current_chunk = ""
                    
                    # 分块处理
                    words = text.split()
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > config.CHUNK_SIZE:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = word
                        else:
                            current_chunk += " " + word if current_chunk else word
                    
                    if current_chunk:
                        chunks.append(current_chunk.strip())
        except Exception as e:
            st.error(f"处理PDF时出错：{str(e)}")
            return []
            
        return chunks
        
    def get_total_pages(self) -> int:
        """获取PDF总页数"""
        if not self.file:
            return 0
            
        with pdfplumber.open(self.file) as pdf:
            return len(pdf.pages)
            
    def process_batch(self, start_page: int, end_page: int) -> List[str]:
        """处理指定页码范围的PDF内容"""
        if not self.file:
            return []
            
        chunks = []
        current_chunk = ""
        
        with pdfplumber.open(self.file) as pdf:
            for page_num in range(start_page, min(end_page, len(pdf.pages))):
                try:
                    page = pdf.pages[page_num]
                    text = page.extract_text() or ""
                    
                    # 分块处理
                    words = text.split()
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > config.CHUNK_SIZE:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = word
                        else:
                            current_chunk += " " + word if current_chunk else word
                except Exception as e:
                    st.error(f"处理第{page_num + 1}页时出错：{str(e)}")
                    continue
                    
            if current_chunk:
                chunks.append(current_chunk.strip())
                
        return chunks
        
    def process(self) -> Generator[List[str], None, None]:
        """分批处理PDF文件"""
        if not self.file:
            yield []
            return
            
        total_pages = self.get_total_pages()
        
        if total_pages > config.MAX_PAGES:
            st.warning(f"文档页数({total_pages})超过限制({config.MAX_PAGES})，将分批处理")
            
        # 分批处理
        batch_size = config.MAX_PAGES
        total_batches = (total_pages + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_page = batch_num * batch_size
            end_page = min(start_page + batch_size, total_pages)
            
            chunks = self.process_batch(start_page, end_page)
            
            # 限制每批次的块数
            if len(chunks) > config.MAX_CHUNKS:
                st.warning(f"内容过多，将只处理前{config.MAX_CHUNKS}个文本块")
                chunks = chunks[:config.MAX_CHUNKS]
                
            yield chunks