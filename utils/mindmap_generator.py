from typing import Optional, Dict, List
import graphviz
import re
from config import UIConfig

class MindmapGenerator:
    """思维导图生成器"""
    def __init__(self):
        """初始化思维导图生成器"""
        self.dot = graphviz.Digraph(
            comment='Paper Summary Mindmap',
            format='png',
            engine='dot',  # 使用dot引擎获得更好的布局
            graph_attr={
                'dpi': '300'  # 在图形属性中设置DPI
            }
        )
        # 设置基本样式
        self.styles = {
            'root': {
                'shape': 'box',
                'style': 'rounded,filled',
                'fillcolor': UIConfig.PRIMARY_COLOR,
                'fontname': UIConfig.FONT_FAMILY,
                'fontcolor': 'white',
                'fontsize': '20',  # 增大字体
                'margin': '0.4,0.2',  # 增加边距
                'width': '2'  # 增加宽度
            },
            'main': {
                'shape': 'box',
                'style': 'rounded,filled',
                'fillcolor': UIConfig.SECONDARY_COLOR,
                'fontname': UIConfig.FONT_FAMILY,
                'fontcolor': 'white',
                'fontsize': '16',  # 增大字体
                'margin': '0.3,0.15',  # 增加边距
                'width': '1.8'  # 增加宽度
            },
            'sub': {
                'shape': 'box',
                'style': 'rounded,filled',
                'fillcolor': UIConfig.ACCENT_COLOR,
                'fontname': UIConfig.FONT_FAMILY,
                'fontcolor': 'white',
                'fontsize': '14',  # 增大字体
                'margin': '0.2,0.1',  # 增加边距
                'width': '1.5'  # 增加宽度
            }
        }
        
    def _extract_key_points(self, text: str) -> Dict[str, List[str]]:
        """提取文本中的关键点"""
        sections = {}
        current_section = None
        current_points = []
        
        # 正则表达式匹配标题和要点
        title_pattern = r'^#+\s+(.+)$'  # 匹配Markdown标题
        point_pattern = r'^[-*]\s+(.+)$'  # 匹配列表项
        key_pattern = r'[【\[](.*?)[】\]]'  # 匹配中括号内的关键词
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是标题
            title_match = re.match(title_pattern, line)
            if title_match:
                if current_section and current_points:
                    sections[current_section] = current_points
                current_section = title_match.group(1)
                current_points = []
                continue
            
            # 检查是否是列表项
            point_match = re.match(point_pattern, line)
            if point_match:
                point = point_match.group(1)
                # 提取关键词
                key_matches = re.findall(key_pattern, point)
                if key_matches:
                    point = ' | '.join(key_matches)
                elif len(point) > UIConfig.MAX_TEXT_LENGTH:
                    # 如果没有关键词标记，截取指定长度
                    point = point[:UIConfig.MAX_TEXT_LENGTH-3] + '...'
                current_points.append(point)
                continue
            
            # 处理普通段落
            if current_section and len(line) > 10:
                # 提取关键句
                sentences = re.split(r'[。！？]', line)
                for sentence in sentences:
                    if len(sentence.strip()) > 10:
                        if len(sentence) > UIConfig.MAX_TEXT_LENGTH:
                            sentence = sentence[:UIConfig.MAX_TEXT_LENGTH-3] + '...'
                        current_points.append(sentence)
        
        # 添加最后一个部分
        if current_section and current_points:
            sections[current_section] = current_points
            
        return sections

    def _clean_text(self, text: str) -> str:
        """清理文本，去除特殊字符"""
        # 移除Markdown标记
        text = re.sub(r'\*\*?(.*?)\*\*?', r'\1', text)
        # 移除其他特殊字符
        text = re.sub(r'[`~!@#$%^&*()+=|{}\[\]:;"\'<>,.?/\\]', ' ', text)
        # 压缩空白字符
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def generate(self, text: str) -> str:
        """生成思维导图"""
        try:
            # 重置图形
            self.dot.clear()
            
            # 设置图形属性
            self.dot.attr(
                rankdir='TB',  # 从上到下的布局
                splines='ortho',  # 使用正交线条
                nodesep='0.8',  # 增加节点间距
                ranksep='1.0',  # 增加层级间距
                dpi='300'  # 在图形属性中设置DPI
            )
            
            # 设置全局属性
            self.dot.attr('node',
                shape='box',
                style='rounded',
                fontname=UIConfig.FONT_FAMILY,
                fontsize='14'
            )
            self.dot.attr('edge',
                color=UIConfig.BORDER_COLOR,
                penwidth='2.0',  # 增加线条宽度
                arrowsize='1.0'  # 增加箭头大小
            )
            
            # 添加根节点
            self.dot.node('root', '论文总结', **self.styles['root'])
            
            # 提取关键点
            sections = self._extract_key_points(text)
            
            # 添加节点和边
            for i, (title, points) in enumerate(sections.items()):
                # 清理标题文本
                title = self._clean_text(title)
                
                # 添加主节点
                main_node = f'main_{i}'
                self.dot.node(main_node, title, **self.styles['main'])
                self.dot.edge('root', main_node)
                
                # 添加子节点
                for j, point in enumerate(points):
                    # 清理要点文本
                    point = self._clean_text(point)
                    if not point:
                        continue
                    
                    sub_node = f'sub_{i}_{j}'
                    self.dot.node(sub_node, point, **self.styles['sub'])
                    self.dot.edge(main_node, sub_node)
            
            return self.dot.source
            
        except Exception as e:
            # 生成错误提示图
            error_dot = graphviz.Digraph()
            error_dot.attr(rankdir='TB')
            error_dot.attr('node', shape='box', style='rounded,filled')
            error_dot.node('root', '思维导图生成失败', fillcolor=UIConfig.ERROR_COLOR)
            error_dot.node('error', str(e), fillcolor=UIConfig.ERROR_COLOR)
            error_dot.edge('root', 'error')
            return error_dot.source

    def export_image(self, dot_source: str, format: str = 'png') -> bytes:
        """导出图片"""
        try:
            # 创建临时图形对象
            tmp_dot = graphviz.Source(dot_source, format=format)
            # 设置导出参数
            tmp_dot.engine = 'dot'  # 使用dot引擎
            # 导出为高质量图片
            return tmp_dot.pipe()
        except Exception as e:
            raise Exception(f"导出图片失败: {str(e)}")