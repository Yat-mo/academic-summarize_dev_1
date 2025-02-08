from typing import List, Dict, Optional
import os
from datetime import datetime
import zipfile
import tempfile
from config import UIConfig

class PaperExporter:
    """论文导出器"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.encoding = UIConfig.FILE_ENCODING
    
    def export_summary(self, summary: Dict) -> str:
        """导出单个总结为Markdown文件"""
        filename = f"{summary['filename']}.md"
        filepath = os.path.join(self.temp_dir, filename)
        
        with open(filepath, 'w', encoding=self.encoding) as f:
            f.write(summary['summary'])
        
        if summary.get('mindmap'):
            img_filename = f"{summary['filename']}_mindmap.png"
            img_filepath = os.path.join(self.temp_dir, img_filename)
            with open(img_filepath, 'wb') as f:
                f.write(summary['mindmap'])
        
        return filepath
    
    def export_batch(self, summaries: List[Dict]) -> bytes:
        """批量导出总结为ZIP文件"""
        try:
            # 创建临时ZIP文件
            zip_path = os.path.join(self.temp_dir, 'summaries.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加每个总结文件
                for summary in summaries:
                    md_path = self.export_summary(summary)
                    arcname = os.path.basename(md_path)
                    zipf.write(md_path, arcname)
                    
                    if summary.get('mindmap'):
                        img_filename = f"{summary['filename']}_mindmap.png"
                        img_filepath = os.path.join(self.temp_dir, img_filename)
                        zipf.write(img_filepath, img_filename)
                    
                # 添加README文件
                readme_content = self._generate_readme(summaries)
                readme_path = os.path.join(self.temp_dir, 'README.md')
                with open(readme_path, 'w', encoding=self.encoding) as f:
                    f.write(readme_content)
                zipf.write(readme_path, 'README.md')
            
            # 读取ZIP文件内容并返回
            with open(zip_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            raise Exception(f"导出失败: {str(e)}")
            
        finally:
            # 清理临时文件
            self._cleanup()
    
    def _generate_readme(self, summaries: List[Dict]) -> str:
        """生成README文件"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        content = f"""# 论文总结导出
        
## 导出信息
- 导出时间：{now}
- 文件数量：{len(summaries)}
- 处理模式：{summaries[0].get('mode', '未知')}
- 文件编码：{self.encoding}

## 文件列表
"""
        
        for summary in summaries:
            content += f"- {summary['filename']}\n"
            
        content += """
## 说明
- 所有文件均为Markdown格式
- 每个文件包含一篇论文的总结
- 总结包含研究背景、方法、结果等关键信息
- 对应的思维导图以PNG格式保存（文件名：论文名_mindmap.png）
"""
        
        return content
    
    def _cleanup(self):
        """清理临时文件"""
        try:
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                if os.path.isfile(filepath):
                    os.unlink(filepath)
            os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")

    def _extract_key_info(self, summary: str) -> dict:
        """从总结文本中提取关键信息 (如创新点、背景、模型优势、结论)
        根据文本中出现相关关键字的信息进行提取，若未找到则返回空字符串
        """
        import re
        key_sections = {"创新点": "", "背景": "", "模型优势": "", "结论": ""}
        # 尝试使用正则表达式根据关键词后跟冒号进行拆分
        # 关键词可以为：创新点、背景、模型优势、结论
        pattern = r'(?P<section>创新点|背景|模型优势|结论)[：:]\s*'
        parts = re.split(pattern, summary)
        # 如果找到了相关关键词，则 parts 列表应为：[前置文本, 关键词, 内容, 关键词, 内容, ...]
        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                section = parts[i]
                content = parts[i+1].strip() if (i+1 < len(parts)) else ""
                if section in key_sections:
                    key_sections[section] = content
        # 如果部分关键词（例如模型优势）未被提取，则回退到按行查找
        for key in key_sections:
            if not key_sections[key]:
                lines = summary.splitlines()
                for index, line in enumerate(lines):
                    if key in line:
                        if index + 1 < len(lines):
                            key_sections[key] = lines[index+1].strip()
                        break

        # 如果"模型优势"这一框依然没有内容，则自动扫描全文根据相关关键词填充
        if not key_sections["模型优势"]:
            # 按中文标点符号分割文本
            sentences = re.split(r'[。；！？\n]', summary)
            candidates = []
            for sentence in sentences:
                # 如果句子中同时包含"模型"以及"优势"或"优点"，则认为该句可能描述了模型优势
                if "模型" in sentence and ("优势" in sentence or "优点" in sentence):
                    candidates.append(sentence.strip())
            if candidates:
                # 拼接所有相关句子，用空格分隔
                key_sections["模型优势"] = " ".join(candidates)

        return key_sections

    def _extract_keywords(self, summary: str) -> str:
        """从总结文本中自动提取关键词，返回以逗号分隔的关键词"""
        import re
        pattern = r'[【\[](.*?)[】\]]'
        matches = re.findall(pattern, summary)
        keywords = list(dict.fromkeys(matches))
        return ", ".join(keywords)

    def export_excel(self, summaries: List[Dict]) -> bytes:
        """批量导出总结为Excel文件，其中包含论文的关键信息(如创新点、背景、模型优势)"""
        import pandas as pd
        import io
        import os
        records = []
        for record in summaries:
            summary_text = record.get("summary", "")
            preview = summary_text[:200] + ("..." if len(summary_text) > 200 else "")
            file_ext = os.path.splitext(record.get("filename", ""))[1].lower().lstrip(".")
            key_info = self._extract_key_info(summary_text)
            keywords = self._extract_keywords(summary_text)
            record_dict = {
                "论文标题": record.get("filename", ""),
                "文件类型": file_ext,
                "关键词": keywords,
                "创新点": key_info.get("创新点", ""),
                "背景": key_info.get("背景", ""),
                "模型优势": key_info.get("模型优势", ""),
                "结论": key_info.get("结论", ""),
                "摘要预览": preview,
                "总结文本": summary_text,
                "总结模式": record.get("mode", "")
            }
            records.append(record_dict)
        
        df = pd.DataFrame(records)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="论文总结")
        return output.getvalue()