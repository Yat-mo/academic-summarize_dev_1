class FileProcessError(Exception):
    """文件处理相关的异常基类"""
    pass

class FileSizeError(FileProcessError):
    """文件大小超出限制"""
    pass

class FileTypeError(FileProcessError):
    """不支持的文件类型"""
    pass

class FileReadError(FileProcessError):
    """文件读取错误"""
    pass

class FileCorruptedError(FileProcessError):
    """文件损坏或格式错误"""
    pass

class PageLimitError(FileProcessError):
    """页数超出限制"""
    pass

class OCRError(FileProcessError):
    """OCR处理错误"""
    pass

class TextExtractionError(FileProcessError):
    """文本提取错误"""
    pass

class TextProcessError(FileProcessError):
    """文本处理错误"""
    pass

class ImageProcessError(FileProcessError):
    """图像处理错误"""
    pass

class ChunkProcessError(FileProcessError):
    """文本分块处理错误"""
    pass

class MergeError(FileProcessError):
    """文本合并错误"""
    pass

class EncodingError(FileProcessError):
    """文本编码错误"""
    pass 