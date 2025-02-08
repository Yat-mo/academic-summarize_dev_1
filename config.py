class APIConfig:
    """API配置"""
    # 并发设置
    MAX_CONCURRENT = 5
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # 秒
    
    # OpenAI配置
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_TEMPERATURE = 0.7
    OPENAI_MAX_TOKENS = 4096
    
    # DeepSeek配置
    DEEPSEEK_MODEL = "deepseek-chat"
    DEEPSEEK_TEMPERATURE = 1.0
    DEEPSEEK_MAX_TOKENS = 4096
    
    @staticmethod
    def get_config(provider: str) -> dict:
        """获取API配置"""
        if provider == "openai":
            return {
                "model": APIConfig.OPENAI_MODEL,
                "temperature": APIConfig.OPENAI_TEMPERATURE,
                "max_tokens": APIConfig.OPENAI_MAX_TOKENS,
                "api_base": "https://api.openai.com/v1"
            }
        elif provider == "deepseek":
            return {
                "model": APIConfig.DEEPSEEK_MODEL,
                "temperature": APIConfig.DEEPSEEK_TEMPERATURE,
                "max_tokens": APIConfig.DEEPSEEK_MAX_TOKENS,
                "api_base": "https://api.deepseek.com/v1"
            }
        else:
            raise ValueError(f"不支持的API提供商: {provider}")

class PDFConfig:
    """PDF处理配置"""
    # 文本处理
    CHUNK_SIZE = 2000
    OVERLAP_SIZE = 150
    MIN_SENTENCE_LENGTH = 10
    MIN_PARAGRAPH_LENGTH = 40
    MAX_TITLE_LENGTH = 100
    
    # OCR设置
    ENABLE_OCR = True  # 是否启用OCR
    OCR_LANGUAGE = "eng+chi_sim+chi_tra"  # OCR语言设置：英文+简体中文+繁体中文
    OCR_DPI = 300  # OCR扫描DPI
    OCR_PSM = 3  # OCR页面分割模式：3=自动分页
    OCR_OEM = 3  # OCR引擎模式：3=默认
    
    # 图片处理
    MIN_IMAGE_SIZE = 100  # 最小图片尺寸（像素）
    MAX_IMAGE_SIZE = 4000  # 最大图片尺寸（像素）
    IMAGE_QUALITY = 95  # JPEG压缩质量
    
    # 文本清理
    REMOVE_EXTRA_SPACES = True  # 移除多余空格
    NORMALIZE_UNICODE = True  # Unicode标准化
    REMOVE_URLS = True  # 移除URL
    REMOVE_EMAILS = True  # 移除邮箱地址
    
    # 处理限制
    MAX_PAGES = 100  # 最大处理页数
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 最大文件大小（50MB）
    TIMEOUT = 300  # 处理超时时间（秒）

class UIConfig:
    """界面配置"""
    # 页面设置
    PAGE_TITLE = "论文批量总结助手"
    PAGE_ICON = "📚"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"
    
    # 主题颜色
    PRIMARY_COLOR = "#1e3a8a"
    SECONDARY_COLOR = "#3b82f6"
    ACCENT_COLOR = "#60a5fa"
    BORDER_COLOR = "#94a3b8"
    ERROR_COLOR = "#ef4444"
    
    # 字体设置
    FONT_FAMILY = "SimSun"
    MAX_TEXT_LENGTH = 40
    FILE_ENCODING = "utf-8"
    
    # 样式
    STYLE = """
    <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stButton button {
            width: 100%;
        }
        .diff-result {
            padding: 1rem;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        /* 思维导图样式 */
        .element-container img {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .streamlit-expanderHeader {
            font-size: 1.1em;
            font-weight: 600;
            color: #1e3a8a;
        }
        /* 下载按钮样式 */
        .stDownloadButton button {
            background-color: #3b82f6;
            color: white;
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            margin: 0.5rem 0;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stDownloadButton button:hover {
            background-color: #1e3a8a;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
    </style>
    """