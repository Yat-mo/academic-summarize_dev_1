import os
from datetime import datetime

class PaperExporter:
    @staticmethod
    def export_markdown(content: str, filename: str) -> str:
        """导出为Markdown文件"""
        if not filename.endswith('.md'):
            filename += '.md'
            
        filepath = os.path.join('exports', filename)
        os.makedirs('exports', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return filepath 