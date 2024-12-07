# OpenAI API配置
OPENAI_MODEL = "gpt-4o-mini-2024-07-18"
MAX_TOKENS = 16384
TEMPERATURE = 0.7
DEFAULT_API_BASE = "https://api.ephone.ai/v1"

# PDF处理配置
CHUNK_SIZE = 8000  # 每个块的最大字符数
CHUNK_OVERLAP = 500  # 块之间的重叠字符数
MAX_CHUNKS = 50  # 增加到50个文本块
MAX_PAGES = 100  # 单次处理的最大页数
MAX_CHARS_PER_CHUNK = 10000

# 进度显示配置
PROGRESS_UPDATE_INTERVAL = 5  # 每处理5页更新一次进度