"""
PDF解析模块 - 提取样例论文的格式信息
"""
import pdfplumber
from typing import List, Dict, Any, Optional
import re


class PDFParser:
    """PDF解析器"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages: List[Dict[str, Any]] = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """解析PDF所有页面"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_info = {
                    "page_num": page_num,
                    "text": page.extract_text() or "",
                    "tables": [],
                    "width": page.width,
                    "height": page.height
                }
                
                # 提取表格
                tables = page.extract_tables()
                for table in tables:
                    page_info["tables"].append({
                        "rows": len(table) if table else 0,
                        "cols": len(table[0]) if table and table[0] else 0,
                        "data": table
                    })
                
                self.pages.append(page_info)
        
        return self.pages
    
    def get_full_text(self) -> str:
        """获取完整文本"""
        return "\n\n".join([p["text"] for p in self.pages])
    
    def extract_format_hints(self) -> Dict[str, Any]:
        """从PDF提取格式提示（简化版）"""
        text = self.get_full_text()
        
        hints = {
            "has_title": False,
            "has_abstract": False,
            "has_keywords": False,
            "has_references": False,
            "estimated_font_size": 12,  # 默认12pt
            "line_spacing": 1.5,  # 默认1.5倍
            "sections": []
        }
        
        # 检测标题（通常在第一页，开头，大字号）
        first_page_text = self.pages[0]["text"] if self.pages else ""
        lines = first_page_text.split("\n")
        
        if lines:
            # 第一行通常为标题
            first_line = lines[0].strip()
            if len(first_line) < 100 and not first_line.endswith("。"):
                hints["has_title"] = True
                hints["sections"].append({"type": "title", "text": first_line})
        
        # 检测摘要
        abstract_patterns = [
            r'摘\s*要',
            r'Abstract',
            r'ABSTRACT'
        ]
        for pattern in abstract_patterns:
            if re.search(pattern, text):
                hints["has_abstract"] = True
                # 提取摘要内容
                match = re.search(f'{pattern}[：:]?\s*([\s\S]*?)(?=关键词|关键字|Keywords)', text)
                if match:
                    hints["sections"].append({
                        "type": "abstract", 
                        "text": match.group(1).strip()[:200]
                    })
                break
        
        # 检测关键词
        keywords_patterns = [
            r'关键词[：:]?\s*([^\n]+)',
            r'关键字[：:]?\s*([^\n]+)',
            r'Keywords[：:]?\s*([^\n]+)'
        ]
        for pattern in keywords_patterns:
            match = re.search(pattern, text)
            if match:
                hints["has_keywords"] = True
                hints["sections"].append({
                    "type": "keywords", 
                    "text": match.group(1).strip()
                })
                break
        
        # 检测参考文献
        ref_patterns = [
            r'参考文献',
            r'References',
            r'REFERENCES'
        ]
        for pattern in ref_patterns:
            if re.search(pattern, text):
                hints["has_references"] = True
                # 提取参考文献条目
                match = re.search(f'{pattern}[\s\S]*', text)
                if match:
                    refs_text = match.group(0)
                    ref_items = re.findall(r'\[\d+\][^\[\]\n]+', refs_text)
                    for item in ref_items[:5]:
                        hints["sections"].append({
                            "type": "reference",
                            "text": item.strip()[:100]
                        })
                break
        
        return hints


def extract_pdf_format(pdf_path: str) -> Dict[str, Any]:
    """便捷函数：提取PDF格式信息"""
    parser = PDFParser(pdf_path)
    parser.parse()
    
    return {
        "full_text": parser.get_full_text(),
        "format_hints": parser.extract_format_hints(),
        "total_pages": len(parser.pages)
    }


def convert_pdf_to_text(pdf_path: str) -> str:
    """便捷函数：PDF转文本"""
    parser = PDFParser(pdf_path)
    return parser.get_full_text()
