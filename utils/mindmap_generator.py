from openai import AsyncOpenAI
import asyncio
import config
import streamlit as st
import graphviz
import json
import os
import tempfile
from graphviz import Source

class MindmapGenerator:
    def __init__(self):
        self.client = None
        
    def generate(self, summary: str) -> str:
        """生成思维导图的DOT语言描述"""
        try:
            status_container = st.empty()
            with status_container:
                status = st.info("正在生成思维导图...")
                # 首先生成思维导图的结构
                mind_map_structure = asyncio.run(self._generate_structure(summary))
                # 然后转换为DOT语言
                dot_content = self._convert_to_dot(mind_map_structure)
                
            return dot_content
            
        except Exception as e:
            st.error(f"思维导图生成失败: {str(e)}")
            return self._get_default_dot()
    
    async def _generate_structure(self, summary: str) -> dict:
        """生成思维导图的结构"""
        if not self.client:
            from utils.openai_handler import OpenAIHandler
            api_key = OpenAIHandler.get_api_key()
            api_base = OpenAIHandler.get_api_base()
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=api_base if api_base else "https://api.openai.com/v1"
            )
        
        try:
            response = await self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的思维导图生成器。请将输入的论文总结转换为思维导图的JSON结构。"
                    },
                    {
                        "role": "user",
                        "content": """请将以下论文总结转换为思维导图结构，要求：
1. 返回严格的JSON格式
2. 不要包含任何其他内容
3. 使用以下固定结构：
{
    "center": "论文标题",
    "main_branches": [
        {
            "title": "分支标题",
            "sub_branches": ["子项1", "子项2"]
        }
    ]
}

论文总结内容如下：

""" + summary
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            try:
                # 尝试解析JSON
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果解析失败，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise
            
        except Exception as e:
            st.error(f"生成结构失败: {str(e)}")
            # 返回默认结构
            return {
                "center": "论文总结",
                "main_branches": [
                    {
                        "title": "生成失败",
                        "sub_branches": ["请重试"]
                    }
                ]
            }
    
    def _convert_to_dot(self, structure: dict) -> str:
        """将结构转换为DOT语言"""
        try:
            dot = graphviz.Digraph()
            dot.attr(rankdir='TB')
            dot.attr('node', 
                    shape='box',
                    style='rounded,filled',
                    fontname='SimSun',
                    margin='0.3,0.1')
            dot.attr('edge', color='#666666', arrowsize='0.8')
            
            # 添加中心节点
            center_id = 'root'
            dot.node(center_id, str(structure.get('center', '论文总结')), fillcolor='#AED6F1')
            
            # 添加主分支
            for i, branch in enumerate(structure.get('main_branches', [])):
                branch_id = f'branch_{i}'
                dot.node(branch_id, str(branch.get('title', '')), fillcolor='#D5F5E3')
                dot.edge(center_id, branch_id)
                
                # 添加子分支
                for j, sub in enumerate(branch.get('sub_branches', [])):
                    sub_id = f'sub_{i}_{j}'
                    dot.node(sub_id, str(sub), fillcolor='#F9E79F')
                    dot.edge(branch_id, sub_id)
            
            return dot.source
            
        except Exception as e:
            st.error(f"DOT转换错误: {str(e)}")
            return self._get_default_dot()
    
    def _get_default_dot(self) -> str:
        """获取默认的DOT图"""
        dot = graphviz.Digraph()
        dot.attr(rankdir='TB')
        dot.attr('node', shape='box', style='rounded,filled')
        
        dot.node('root', '思维导图生成失败', fillcolor='#FFE6E6')
        dot.node('error', '请重试', fillcolor='#FFE6E6')
        dot.edge('root', 'error')
        
        return dot.source
    
    def export_image(self, dot_content: str, format: str = 'png') -> bytes:
        """导出思维导图为图片"""
        try:
            # 创建新的Digraph
            dot = graphviz.Digraph()
            
            # 设置基本属性
            dot.attr(
                'graph',
                rankdir='TB',
                bgcolor='transparent',
                dpi='300',
                size='12,8!',
                ratio='compress'
            )
            
            # 设置节点和边的默认样式
            dot.attr('node', 
                    shape='box',
                    style='rounded,filled',
                    fontname='SimSun',
                    margin='0.3,0.1')
            dot.attr('edge', color='#666666', arrowsize='0.8')
            
            # 解析原始DOT内容
            import re
            
            # 移除全局属性设置行
            content_lines = dot_content.split('\n')
            filtered_lines = []
            for line in content_lines:
                # 跳过全局属性设置行
                if 'node [' in line or 'edge [' in line:
                    continue
                # 跳过空行和注释
                if not line.strip() or line.strip().startswith('//'):
                    continue
                filtered_lines.append(line)
            
            # 重新组合内容
            cleaned_content = '\n'.join(filtered_lines)
            
            # 提取节点定义
            node_pattern = r'(\w+)\s*\[([^\]]+)\]'
            nodes = re.findall(node_pattern, cleaned_content)
            for node_id, attrs in nodes:
                # 解析节点属性
                attr_dict = {}
                for attr in attrs.split(','):
                    if '=' in attr:
                        key, value = attr.split('=', 1)
                        # 去除多余的引号和空格
                        key = key.strip()
                        value = value.strip().strip('"')
                        # 只保留需要的属性
                        if key in ['label', 'fillcolor']:
                            attr_dict[key] = value
                dot.node(node_id, **attr_dict)
            
            # 提取边定义
            edge_pattern = r'(\w+)\s*->\s*(\w+)'
            edges = re.findall(edge_pattern, cleaned_content)
            for src, dst in edges:
                dot.edge(src, dst)
            
            # 生成图片
            image_data = dot.pipe(format=format)
            return image_data
            
        except Exception as e:
            st.error(f"图片生成失败: {str(e)}")
            # 返回一个简单的错误图片
            error_dot = graphviz.Digraph()
            error_dot.attr(
                'graph',
                rankdir='TB',
                bgcolor='transparent'
            )
            error_dot.node(
                'error',
                '导出失败\n请重试',
                shape='box',
                style='filled',
                fillcolor='#FFE6E6',
                fontname='SimSun'
            )
            return error_dot.pipe(format=format)