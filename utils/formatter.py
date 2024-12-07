import re
from typing import Dict, Any
import pandas as pd

class PaperFormatter:
    @staticmethod
    def format_summary(summary_data: Dict[str, Any]) -> str:
        """将论文总结格式化为Markdown格式"""
        md = f"""# {summary_data['title']}

## 1. 基本信息
- 发表时间：{summary_data.get('publish_date', 'N/A')}
- 作者：{summary_data.get('authors', 'N/A')}
- 关键词：{', '.join(summary_data.get('keywords', []))}

## 2. 研究概述
> 核心问题：{summary_data.get('core_problem', 'N/A')}
> 主要贡献：{summary_data.get('main_contributions', 'N/A')}

### 2.1 研究背景
{summary_data.get('background', 'N/A')}

### 2.2 研究目标
{summary_data.get('objectives', 'N/A')}

## 3. 技术方案
### 3.1 创新点
{PaperFormatter._format_list(summary_data.get('innovations', []))}

### 3.2 具体实现
{summary_data.get('implementation', 'N/A')}

## 4. 实验结果
### 4.1 实验设置
{PaperFormatter._format_table(summary_data.get('experiment_settings', {}))}

### 4.2 性能评估
{PaperFormatter._format_list(summary_data.get('performance_metrics', []))}

## 5. 主要结论
{PaperFormatter._format_list(summary_data.get('conclusions', []))}

## 6. 研究局限
{PaperFormatter._format_list(summary_data.get('limitations', []))}

---
*注：本总结基于论文 {summary_data.get('paper_url', '')}*
"""
        return md

    @staticmethod
    def _format_list(items: list) -> str:
        """格式化列表项"""
        if not items:
            return "N/A"
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def _format_table(data: Dict[str, Any]) -> str:
        """格式化表格数据"""
        if not data:
            return "N/A"
        
        df = pd.DataFrame(data)
        return df.to_markdown(index=False)

    @staticmethod
    def extract_tables(text: str) -> pd.DataFrame:
        """从文本中提取表格数据"""
        # 使用正则表达式匹配表格格式
        table_pattern = r'\|.*\|'
        tables = re.findall(table_pattern, text, re.MULTILINE)
        if tables:
            # 转换为pandas DataFrame
            return pd.read_csv(pd.io.common.StringIO('\n'.join(tables)), sep='|')
        return pd.DataFrame() 