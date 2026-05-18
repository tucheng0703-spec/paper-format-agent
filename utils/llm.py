"""
LLM调用模块 - 格式理解、规则提取
"""
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from config import SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, LLM_MODEL


# Prompt 1: 格式要求理解
PROMPT_FORMAT_UNDERSTANDING = """你是一个专业的学术论文格式规范专家。请分析以下格式要求文本，提取出结构化的格式规则。

## 格式要求文本：
{format_requirements}

## 输出要求：
请严格按照以下JSON格式输出，不要添加任何解释或额外文字：

```json
{{
    "title_rules": [
        {{
            "target": "title",
            "font_name": "字体名称，如宋体、黑体等",
            "font_size": 字号数字,
            "bold": true或false,
            "alignment": "对齐方式:left/center/right/justify",
            "space_after": 段后间距数字,
            "space_before": 段前间距数字
        }}
    ],
    "abstract_rules": [
        {{
            "target": "abstract",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "bold": false,
            "alignment": "justify",
            "line_spacing": 行距数字,
            "first_line_indent": 首行缩进字符数,
            "space_before": 数字,
            "space_after": 数字
        }}
    ],
    "keywords_rules": [
        {{
            "target": "keywords",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "space_before": 数字,
            "space_after": 数字
        }}
    ],
    "body_rules": [
        {{
            "target": "body",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "bold": false,
            "alignment": "justify",
            "line_spacing": 行距数字,
            "first_line_indent": 首行缩进字符数,
            "space_before": 数字,
            "space_after": 数字
        }}
    ],
    "reference_rules": [
        {{
            "target": "reference",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "alignment": "left",
            "line_spacing": 行距数字,
            "first_line_indent": 0,
            "space_before": 数字,
            "space_after": 数字
        }}
    ]
}}
```

注意：
1. 如果某项格式要求没有明确说明，不要写null，保持该项不存在
2. 中文字体请使用：宋体、黑体、楷体、仿宋、微软雅黑
3. 行距如果要求"1.5倍行距"请写1.5，"2倍行距"写2
4. 首行缩进：如果要求"首行缩进2字符"请写2
5. 字号单位是磅(pt)
"""


# Prompt 2: 样例论文格式逆向提取
PROMPT_SAMPLE_EXTRACTION = """你是一个专业的学术论文格式规范专家。请分析以下样例论文的格式信息，逆向提取出完整的格式规则。

## 样例论文各部分的格式信息：

### 标题部分（{title_count}个段落）：
{title_info}

### 摘要部分（{abstract_count}个段落）：
{abstract_info}

### 关键词部分（{keywords_count}个段落）：
{keywords_info}

### 正文部分（{body_count}个段落，选取前5个代表性段落）：
{body_info}

### 参考文献部分（{reference_count}个段落，选取前5个代表性条目）：
{reference_info}

## 输出要求：
请提取出每种类型段落的通用格式规则，输出格式如下：

```json
{{
    "title_rules": [
        {{
            "target": "title",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "bold": true或false,
            "alignment": "对齐方式:left/center/right/justify",
            "space_before": 数字,
            "space_after": 数字
        }}
    ],
    "abstract_rules": [
        {{
            "target": "abstract",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "alignment": "对齐方式",
            "line_spacing": 行距数字,
            "first_line_indent": 首行缩进字符数,
            "space_before": 数字,
            "space_after": 数字
        }}
    ],
    "keywords_rules": [
        {{
            "target": "keywords",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "space_before": 数字,
            "space_after": 数字
        }}
    ],
    "body_rules": [
        {{
            "target": "body",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "bold": false,
            "alignment": "justify",
            "line_spacing": 行距数字,
            "first_line_indent": 首行缩进字符数,
            "space_before": 数字,
            "space_after": 数字
        }}
    ],
    "reference_rules": [
        {{
            "target": "reference",
            "font_name": "字体名称",
            "font_size": 字号数字,
            "alignment": "left",
            "line_spacing": 行距数字,
            "first_line_indent": 0,
            "space_before": 数字,
            "space_after": 数字
        }}
    ]
}}
```

注意：
1. 如果某个字段在样例中没有明确体现，不要写，保持该项不存在
2. 中文字体名称使用标准名称
3. 如果某段落格式特殊（如标题样式与正文不同），请单独列出
"""


def format_paragraphs_info(paragraphs: List[Dict]) -> str:
    """格式化段落信息用于prompt"""
    if not paragraphs:
        return "（无）"
    
    info_parts = []
    for i, p in enumerate(paragraphs[:10], 1):  # 最多10个
        info = f"{i}. 文本: {p.get('text', '')[:50]}..."
        info += f"\n   样式: {p.get('style_name', 'Normal')}"
        info += f"\n   字体: {p.get('font_name', '宋体')}, {p.get('font_size', 12)}磅"
        info += f"\n   加粗: {p.get('bold', False)}, 斜体: {p.get('italic', False)}"
        info += f"\n   对齐: {p.get('alignment', 'left')}"
        info += f"\n   行距: {p.get('line_spacing', 1.5)}倍, 首行缩进: {p.get('first_line_indent', 0)}字符"
        info += f"\n   段前: {p.get('space_before', 0)}磅, 段后: {p.get('space_after', 0)}磅"
        info_parts.append(info)
    
    return "\n".join(info_parts)


class LLMClient:
    """LLM客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or SILICONFLOW_API_KEY
        self.base_url = base_url or SILICONFLOW_BASE_URL
        self.model = model or LLM_MODEL
        
        if not self.api_key:
            raise ValueError("API Key未配置，请在.env文件中设置SILICONFLOW_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def extract_rules_from_requirements(self, format_requirements: str) -> Dict[str, Any]:
        """从格式要求文本提取规则"""
        prompt = PROMPT_FORMAT_UNDERSTANDING.format(
            format_requirements=format_requirements
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的学术论文格式规范专家，擅长提取和整理论文格式要求。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # 提取JSON
        return self._extract_json(content)
    
    def extract_rules_from_sample(self, sample_info: Dict[str, List]) -> Dict[str, Any]:
        """从样例论文提取规则"""
        prompt = PROMPT_SAMPLE_EXTRACTION.format(
            title_count=len(sample_info.get("title", [])),
            title_info=format_paragraphs_info(sample_info.get("title", [])),
            abstract_count=len(sample_info.get("abstract", [])),
            abstract_info=format_paragraphs_info(sample_info.get("abstract", [])),
            keywords_count=len(sample_info.get("keywords", [])),
            keywords_info=format_paragraphs_info(sample_info.get("keywords", [])),
            body_count=len(sample_info.get("body", [])),
            body_info=format_paragraphs_info(sample_info.get("body", [])),
            reference_count=len(sample_info.get("reference", [])),
            reference_info=format_paragraphs_info(sample_info.get("reference", [])),
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的学术论文格式规范专家，擅长从样例论文中逆向提取格式规则。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content.strip()
        
        # 提取JSON
        return self._extract_json(content)
    
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """从响应中提取JSON"""
        # 尝试找到JSON块
        import re
        
        # 匹配 ```json ... ``` 块
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试匹配 ``` ... ``` 或直接的大括号
            json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 直接查找JSON对象
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = content
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM返回的JSON格式无效: {str(e)}\n原始内容: {content[:500]}")
    
    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """通用聊天接口"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()


# 全局客户端实例（延迟初始化）
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取LLM客户端实例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
