# 论文批量总结助手 📚

一个基于AI的论文批量总结工具，支持PDF和Word文档的自动分析和总结。

## ✨ 主要特性

- 🚀 支持批量处理多个文档
- 📄 支持PDF和Word格式
- 🤖 智能文本提取和OCR支持
- 💡 多种总结模式（简洁/标准/详细）
- 📊 思维导图可视化
- 🔄 批量导出功能
- 🎨 美观的Web界面

## 🛠️ 系统要求

- Python 3.8+
- 操作系统：Windows/macOS/Linux
- 可选：Tesseract-OCR（用于OCR功能）

## 📥 详细安装步骤

### 🔰 1. 环境准备

1. 安装Python（3.8或更高版本）：
   - Windows：从[Python官网](https://www.python.org/downloads/)下载安装
   - macOS：`brew install python3`
   - Ubuntu：`sudo apt-get install python3`

2. 安装pip（如果尚未安装）：
   - Windows：Python安装时通常会包含pip
   - macOS/Linux：`curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py`

### 📦 2. 获取项目代码

1. 克隆仓库：
```bash
git clone https://github.com/Yat-mo/academic-summarize_dev_2
cd academic-summarize_dev_2
```

2. 创建虚拟环境（推荐）：
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 🔧 3. 安装依赖

1. 更新pip：
```bash
pip install --upgrade pip
```

2. 安装项目依赖：
```bash
pip install -r requirements.txt
```

### 🔑 4. API配置

1. 创建配置文件：
- 在项目根目录下创建一个名为`.env`的文件。

2. 配置API密钥：
- 在`.env`文件，填入以下内容：
```env
# OpenAI API配置
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_API_BASE=https://api.openai.com/v1  # 如果使用代理，替换为代理地址

# DeepSeek API配置
DEEPSEEK_API_KEY=你的DeepSeek API密钥
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

注意事项：
- 🌐 OpenAI API密钥获取：访问[OpenAI平台](https://platform.openai.com/)注册并创建API密钥
- 🔐 DeepSeek API密钥获取：访问[DeepSeek平台](https://platform.deepseek.com/)注册并创建API密钥
- 🌍 如果使用国内代理服务，需要将API_BASE替换为对应的代理地址

### 📸 5. （可选）OCR配置（注意安装很慢，耐心等待，不用安装也能用。）

1. 安装Tesseract-OCR：

Windows：
- 从[GitHub](https://github.com/UB-Mannheim/tesseract/wiki)下载安装包
- 安装时记住安装路径
- 将安装路径添加到系统环境变量PATH中

macOS：
```bash
brew install tesseract
brew install tesseract-lang  # 安装额外语言包
```

Ubuntu：
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim  # 中文简体支持
sudo apt-get install tesseract-ocr-chi-tra  # 中文繁体支持
```

2. 验证安装：
```bash
tesseract --version
```

### 🚀 6. 启动应用

1. 激活虚拟环境（如果使用）：
```bash
# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. 启动应用：
```bash
streamlit run app.py
```

3. 访问应用：
   打开浏览器访问 http://localhost:8501

## 📖 使用说明

1. 📤 上传一个或多个PDF/Word文件
   - 📋 选择总结模式（简洁/标准/详细）
   - ▶️ 点击"开始总结"
   - ⏳ 等待处理完成
   - 📥 查看结果并下载

## 🎯 功能说明

### 📝 总结模式
- 💡 **简洁模式**：约800字，突出核心观点和主要结论
- 📊 **标准模式**：约1500字，包含研究方法、结果和讨论
- 📚 **详细模式**：约2500字，深入分析研究背景、方法、结果和影响

### ⚙️ 文本处理
- 🤖 智能文本提取
- 📷 OCR支持（需安装Tesseract）
- 📑 自动分块处理
- 🌏 多语言支持

### 📤 输出格式
- 📋 Markdown格式
- 🎯 思维导图
- 📦 批量导出

## ⚙️ 配置说明

主要配置文件：
- 🔧 `config.py`：系统配置
- 🔐 `.env`：API密钥配置
- 📝 `prompts.py`：提示词模板

可配置项包括：
- ⚡ API设置（模型、温度等）
- 📊 文本处理参数
- 🎨 UI主题
- 📸 OCR设置
- 💾 缓存设置

## ⚠️ 注意事项

1. 🔑 API使用：
   - 💰 请确保有足够的API额度
   - 🌐 建议使用代理以提高访问速度

2. 📄 文件处理：
   - 📦 支持的最大文件大小：50MB
   - 📚 支持的最大页数：100页
   - ⏱️ OCR处理会显著增加处理时间

3. ⚡ 性能优化：
   - 💾 使用缓存减少API调用
   - 🚀 并发处理提高效率
   - 📊 大文件建议分批处理

## 📄 许可证

MIT License

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目。
