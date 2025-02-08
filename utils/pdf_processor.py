import io
import os
import fitz  # PyMuPDF package provides the fitz module
import pytesseract
from PIL import Image
import numpy as np
from typing import List, Dict, Optional
from .file_processor import BaseFileProcessor
from .exceptions import (
    FileProcessError,
    FileCorruptedError,
    PageLimitError,
    OCRError,
    ImageProcessError,
    TextExtractionError,
    TextProcessError
)
from config import PDFConfig

class PDFProcessor(BaseFileProcessor):
    """PDF文件处理器"""
    
    def __init__(self):
        """初始化PDF处理器"""
        super().__init__()
        # 初始化OCR
        if PDFConfig.ENABLE_OCR:
            try:
                pytesseract.pytesseract.tesseract_cmd = 'tesseract'
                # 测试OCR是否可用
                test_img_path = os.path.join(os.path.dirname(__file__), 'test.png')
                Image.new('RGB', (1, 1)).save(test_img_path)
                pytesseract.image_to_string(test_img_path)
                os.remove(test_img_path)
            except Exception as e:
                raise OCRError(f"OCR初始化失败: {str(e)}")
    
    def _extract_text_from_file(self, file) -> str:
        """从PDF文件中提取文本"""
        try:
            # 读取文件内容
            file_content = file.read()
            
            # 打开PDF文档
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
            except Exception as e:
                raise FileCorruptedError(f"PDF文件格式错误: {str(e)}")
            
            try:
                # 检查页数
                if len(doc) > PDFConfig.MAX_PAGES:
                    raise PageLimitError(
                        f"页数超过限制: {len(doc)} > {PDFConfig.MAX_PAGES}"
                    )
                
                text_content = []
                
                for page_num in range(len(doc)):
                    try:
                        # 获取页面文本
                        page_text = self._process_page(doc[page_num])
                        if page_text:
                            text_content.append(page_text)
                    except Exception as e:
                        raise TextProcessError(f"第{page_num+1}页处理失败: {str(e)}")
                
                if not text_content:
                    raise TextExtractionError("PDF文档内容为空")
                
                return '\n\n'.join(text_content)
                
            finally:
                doc.close()
                
        except FileProcessError:
            raise
        except Exception as e:
            raise TextExtractionError(f"PDF文本提取失败: {str(e)}")
    
    def _process_page(self, page) -> str:
        """处理单个PDF页面"""
        try:
            # 提取文本
            text = page.get_text()
            
            # 如果页面没有文本且启用了OCR，进行OCR处理
            if not text.strip() and PDFConfig.ENABLE_OCR:
                text = self._process_page_ocr(page)
            
            # 清理文本
            return self._clean_text(text)
            
        except FileProcessError:
            raise
        except Exception as e:
            raise TextExtractionError(f"页面处理失败: {str(e)}")
    
    def _process_page_ocr(self, page) -> str:
        """对页面进行OCR处理"""
        try:
            # 获取页面图像
            try:
                pix = page.get_pixmap(dpi=PDFConfig.OCR_DPI)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            except Exception as e:
                raise ImageProcessError(f"页面图像提取失败: {str(e)}")
            
            # 处理图像
            img = self._process_image(img)
            
            # 进行OCR识别
            try:
                text = pytesseract.image_to_string(
                    img,
                    lang=PDFConfig.OCR_LANGUAGE,
                    config=f'--psm {PDFConfig.OCR_PSM} --oem {PDFConfig.OCR_OEM}'
                )
                
                if not text.strip():
                    # 如果识别结果为空，尝试不同的PSM模式
                    for psm in [1, 4, 6]:
                        text = pytesseract.image_to_string(
                            img,
                            lang=PDFConfig.OCR_LANGUAGE,
                            config=f'--psm {psm} --oem {PDFConfig.OCR_OEM}'
                        )
                        if text.strip():
                            break
                
                if not text.strip():
                    raise OCRError("OCR识别结果为空")
                    
                return text
                
            except Exception as e:
                raise OCRError(f"OCR识别失败: {str(e)}")
                
        except FileProcessError:
            raise
        except Exception as e:
            raise OCRError(f"OCR处理失败: {str(e)}")
    
    def _process_image(self, img: Image.Image) -> Image.Image:
        """处理图像以优化OCR效果"""
        try:
            # 转换为灰度图
            try:
                img = img.convert('L')
            except Exception as e:
                raise ImageProcessError(f"图像转换失败: {str(e)}")
            
            # 调整大小
            img = self._resize_image(img)
            
            # 二值化处理
            img = self._binarize_image(img)
            
            return img
            
        except FileProcessError:
            raise
        except Exception as e:
            raise ImageProcessError(f"图像处理失败: {str(e)}")
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """调整图像大小"""
        try:
            width, height = img.size
            
            # 检查是否需要调整大小
            if width > PDFConfig.MAX_IMAGE_SIZE or height > PDFConfig.MAX_IMAGE_SIZE:
                ratio = min(PDFConfig.MAX_IMAGE_SIZE / width, PDFConfig.MAX_IMAGE_SIZE / height)
                new_size = (int(width * ratio), int(height * ratio))
                return img.resize(new_size, Image.LANCZOS)
            elif width < PDFConfig.MIN_IMAGE_SIZE or height < PDFConfig.MIN_IMAGE_SIZE:
                ratio = max(PDFConfig.MIN_IMAGE_SIZE / width, PDFConfig.MIN_IMAGE_SIZE / height)
                new_size = (int(width * ratio), int(height * ratio))
                return img.resize(new_size, Image.LANCZOS)
            
            return img
            
        except Exception as e:
            raise ImageProcessError(f"图像大小调整失败: {str(e)}")
    
    def _binarize_image(self, img: Image.Image) -> Image.Image:
        """图像二值化处理"""
        try:
            img_array = np.array(img)
            binary = (img_array > 128) * 255
            return Image.fromarray(binary.astype('uint8'))
            
        except Exception as e:
            raise ImageProcessError(f"图像二值化处理失败: {str(e)}")