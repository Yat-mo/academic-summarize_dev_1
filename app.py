import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
import pandas as pd
import difflib
import zipfile
import tempfile
from datetime import datetime
from utils.pdf_processor import PDFProcessor
from utils.word_processor import WordProcessor
from utils.openai_handler import AIHandler
from utils.mindmap_generator import MindmapGenerator
from utils.exporter import PaperExporter
from utils.batch_processor import BatchProcessor
from utils.file_processor import BaseFileProcessor
from config import APIConfig, UIConfig, PDFConfig
from prompts import get_prompts

def set_page_style():
    st.set_page_config(
        page_title=UIConfig.PAGE_TITLE,
        page_icon=UIConfig.PAGE_ICON,
        layout=UIConfig.LAYOUT,
        initial_sidebar_state=UIConfig.INITIAL_SIDEBAR_STATE
    )
    st.markdown(UIConfig.STYLE, unsafe_allow_html=True)

class PaperSummarizer:
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        set_page_style()
        self.setup_sidebar()
        self.initialize_session_state()
        
    def setup_sidebar(self):
        st.sidebar.title("⚙️ 设置")
        
        # 添加API提供商选择
        self.api_provider = st.sidebar.selectbox(
            "API 提供商",
            ["OpenAI", "DeepSeek"],
            help="选择API服务提供商"
        ).lower()
        
        # 从环境变量或session_state获取API密钥
        env_key = f"{self.api_provider.upper()}_API_KEY"
        default_api_key = os.getenv(env_key, "")
        
        # 为每个提供商维护独立的API密钥
        if f"{self.api_provider}_api_key" not in st.session_state:
            st.session_state[f"{self.api_provider}_api_key"] = default_api_key
        
        api_key = st.sidebar.text_input(
            f"{self.api_provider.title()} API Key", 
            type="password",
            value=st.session_state[f"{self.api_provider}_api_key"],
            key=f"{self.api_provider}_key_input"
        )
        
        if api_key != st.session_state[f"{self.api_provider}_api_key"]:
            st.session_state[f"{self.api_provider}_api_key"] = api_key
        
        # 更新当前使用的API密钥
        st.session_state.api_key = st.session_state[f"{self.api_provider}_api_key"]
        
        # 从环境变量或session_state获取API基础URL
        config = APIConfig.get_config(self.api_provider)
        default_api_base = os.getenv(f"{self.api_provider.upper()}_API_BASE", config["api_base"])
        
        # 为每个提供商维护独立的API基础URL
        if f"{self.api_provider}_api_base" not in st.session_state:
            st.session_state[f"{self.api_provider}_api_base"] = default_api_base
        
        api_base = st.sidebar.text_input(
            "API Base URL",
            value=st.session_state[f"{self.api_provider}_api_base"],
            key=f"{self.api_provider}_base_input"
        )
        
        if api_base != st.session_state[f"{self.api_provider}_api_base"]:
            st.session_state[f"{self.api_provider}_api_base"] = api_base
        
        # 更新当前使用的API基础URL
        st.session_state.api_base = st.session_state[f"{self.api_provider}_api_base"]
        
        # 添加总结模式选择
        self.summary_mode = st.sidebar.radio(
            "📝 总结模式",
            ["简洁模式", "标准模式", "详细模式"],
            help="选择总结的详细程度"
        )
        
        # 显示模式说明
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        ### 模式说明
        
        🔹 **简洁模式**
        - 提供论文的核心观点和主要结论
        - 适合快速了解论文要点
        - 总结长度约800字
        
        🔹 **标准模式**
        - 包含研究方法、结果和讨论
        - 适合深入理解研究内容
        - 总结长度约1500字
        
        🔹 **详细模式**
        - 深入分析研究背景、方法、结果和影响
        - 适合全面掌握论文内容
        - 总结长度约2500字
        """)
        
        # 添加高级设置折叠面板
        with st.sidebar.expander("🛠️ 高级设置"):
            # 并发设置
            st.write("#### 并发设置")
            max_concurrent = st.slider(
                "最大并发请求数",
                min_value=1,
                max_value=10,
                value=APIConfig.MAX_CONCURRENT,
                help="同时处理的最大文本块数量"
            )
            
            # 文本处理设置
            st.write("#### 文本处理设置")
            chunk_size = st.slider(
                "文本块大小",
                min_value=500,
                max_value=3000,
                value=PDFConfig.CHUNK_SIZE,
                help="单个文本块的最大字符数"
            )
            
            # 模型参数设置
            st.write("#### 模型参数")
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=config["temperature"],
                step=0.1,
                help="控制输出的随机性"
            )
        
        # 存设置到session_state
        if "settings" not in st.session_state:
            st.session_state.settings = {}
        
        st.session_state.settings.update({
            "max_concurrent": max_concurrent,
            "chunk_size": chunk_size,
            "temperature": temperature
        })
        
    def initialize_session_state(self):
        """初始化会话状态"""
        if "history" not in st.session_state:
            st.session_state.history = []
        if "processing" not in st.session_state:
            st.session_state.processing = False
        if "ai_handler" not in st.session_state:
            st.session_state.ai_handler = None
            
    async def process_paper(self, file):
        """处理单个论文文件"""
        try:
            # 创建状态容器
            status_container = st.empty()
            with status_container:
                st.info(f"正在处理：{file.name}")
            
            # 获取文件处理器
            processor = BaseFileProcessor.get_processor(file.name)
            
            # 提取文本
            text_chunks = processor.extract_text(file)
            
            # 初始化或更新AI处理器
            if not st.session_state.ai_handler:
                st.session_state.ai_handler = AIHandler(
                    api_key=st.session_state.api_key,
                    api_base=st.session_state.api_base,
                    provider=self.api_provider
                )
            
            # 获取提示词
            prompts = get_prompts(self.summary_mode)
            
            # 创建批处理器
            batch_processor = BatchProcessor(
                max_workers=st.session_state.settings["max_concurrent"],
                progress_callback=lambda p, d: status_container.progress(p)
            )
            
            # 批量处理文本块
            with status_container:
                st.info("正在分析文本块...")
            
            summaries = await batch_processor.process_batch(
                text_chunks,
                lambda chunk: st.session_state.ai_handler.process_text(
                    chunk,
                    prompts["summary_prompt"]
                ),
                description="正在总结文本块"
            )
            
            if not summaries:
                raise Exception("文本块处理失败")
            
            # 合并所有总结
            with status_container:
                st.info("正在合并总结...")
            
            merged_summary = await st.session_state.ai_handler.process_text(
                "\n\n".join(summaries),
                prompts["merge_prompt"]
            )
            
            if not merged_summary:
                raise Exception("总结合并失败")
            
            # 使用专门的final_summary_prompt生成最终总结
            with status_container:
                st.info("正在生成最终总结...")
            
            final_summary = await st.session_state.ai_handler.process_text(
                merged_summary,
                prompts["final_summary_prompt"]
            )
            
            if not final_summary:
                raise Exception("最终总结生成失败")
            
            # 组合最终内容
            complete_summary = f"""# {file.name} 论文总结

{final_summary}"""
            
            # 生成思维导图
            with status_container:
                st.info("正在生成思维导图...")
            
            mindmap_generator = MindmapGenerator()
            try:
                dot_source = mindmap_generator.generate(complete_summary)
                mindmap_image = mindmap_generator.export_image(dot_source, 'png')
            except Exception as e:
                st.error(f"思维导图生成失败：{str(e)}")
                mindmap_image = None
            
            # 保存到历史记录
            st.session_state.history.append({
                "filename": file.name,
                "summary": complete_summary,
                "mode": self.summary_mode,
                "timestamp": pd.Timestamp.now(),
                "mindmap": mindmap_image
            })
            
            # 完成处理
            with status_container:
                st.success(f"✅ 完成：{file.name}")
            
        except Exception as e:
            error_msg = str(e)
            with status_container:
                if "API配额不足" in error_msg:
                    st.error("😢 API配额不足，请检查账户余额")
                elif "API密钥无效" in error_msg:
                    st.error("🔑 API密钥无效，请检查配置")
                elif "模型不可用" in error_msg:
                    st.error("⚠️ 模型不可用，请尝试其他模型")
                else:
                    st.error(f"❌ 处理失败：{error_msg}")
            return None

    async def main(self):
        st.title("论文批量总结助手 📚")
        
        uploaded_files = st.file_uploader(
            "拖拽文件到这里或点击上传",
            type=['pdf', 'doc', 'docx'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("开始总结", use_container_width=True):
                    if not st.session_state.api_key:
                        st.error("请先设置API Key")
                        return
                    
                    st.session_state.processing = True
                    for file in uploaded_files:
                        try:
                            await self.process_paper(file)
                        except Exception as e:
                            st.error(f"处理失败：{str(e)}")
                            continue
                    st.session_state.processing = False
        
        # 历史记录区域
        if st.session_state.history:
            # 添加批量下载按钮
            col1, col2, col3 = st.columns([2, 2, 2])
            with col2:
                # 创建导出器实例
                exporter = PaperExporter()
                # 导出所有总结为ZIP
                zip_data = exporter.export_batch(st.session_state.history)
                st.download_button(
                    "📥 下载所有总结 (ZIP)",
                    zip_data,
                    "paper_summaries.zip",
                    "application/zip",
                    key="download_all_btn",
                    use_container_width=True,
                )
                # 添加Excel导出按钮
                excel_data = exporter.export_excel(st.session_state.history)
                st.download_button(
                    "📥 下载所有总结 (Excel)",
                    excel_data,
                    "paper_summaries.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_btn",
                    use_container_width=True,
                )
            
            st.markdown("## 历史记录")
            
            # 显示历史记录
            for i, record in enumerate(st.session_state.history):
                with st.container():
                    col1, col2 = st.columns([3,1])
                    with col1:
                        st.subheader(record['filename'])
                    with col2:
                        st.text(record['timestamp'].strftime('%Y-%m-%d %H:%M'))
                    
                    st.markdown(
                        f'<div class="diff-result">{record["summary"]}</div>',
                        unsafe_allow_html=True
                    )
                    
                    # 显示思维导图
                    if record.get("mindmap"):
                        # 创建两列布局
                        img_col, btn_col = st.columns([4, 1])
                        with img_col:
                            # 使用expander来控制思维导图的显示
                            with st.expander("📊 思维导图", expanded=True):
                                st.image(
                                    record["mindmap"],
                                    caption="思维导图预览",
                                    use_column_width=True,
                                    output_format="PNG"
                                )
                        with btn_col:
                            # 添加思维导图下载按钮
                            st.download_button(
                                "⬇️ 下载思维导图",
                                record["mindmap"],
                                f"{record['filename']}_mindmap.png",
                                mime="image/png",
                                key=f"download_mindmap_{i}"
                            )
                    
                    # 下载单个文件按钮
                    st.download_button(
                        "📄 下载此总结",
                        record['summary'],
                        f"{record['filename']}.md",
                        key=f"download_btn_{i}"
                    )

if __name__ == "__main__":
    app = PaperSummarizer()
    asyncio.run(app.main()) 