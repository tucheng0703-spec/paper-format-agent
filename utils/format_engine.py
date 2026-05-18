"""
格式规则引擎 - 核心模块
定义格式规则的数据结构和应用逻辑
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json


@dataclass
class FormatRule:
    """格式规则定义"""
    target: str  # "title" / "abstract" / "body" / "reference" / "figure" / "table"
    font_name: Optional[str] = None  # 字体
    font_size: Optional[float] = None  # 字号（磅）
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    alignment: Optional[str] = None  # left/center/justify/right
    line_spacing: Optional[float] = None  # 行距（倍数）
    first_line_indent: Optional[float] = None  # 首行缩进（字符数）
    space_before: Optional[float] = None  # 段前间距（磅）
    space_after: Optional[float] = None  # 段后间距（磅）
    page_break_before: Optional[bool] = None  # 分页符
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormatRule':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class RuleSet:
    """规则集"""
    title_rules: List[FormatRule] = field(default_factory=list)
    abstract_rules: List[FormatRule] = field(default_factory=list)
    keywords_rules: List[FormatRule] = field(default_factory=list)
    body_rules: List[FormatRule] = field(default_factory=list)
    reference_rules: List[FormatRule] = field(default_factory=list)
    figure_rules: List[FormatRule] = field(default_factory=list)
    table_rules: List[FormatRule] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title_rules": [r.to_dict() for r in self.title_rules],
            "abstract_rules": [r.to_dict() for r in self.abstract_rules],
            "keywords_rules": [r.to_dict() for r in self.keywords_rules],
            "body_rules": [r.to_dict() for r in self.body_rules],
            "reference_rules": [r.to_dict() for r in self.reference_rules],
            "figure_rules": [r.to_dict() for r in self.figure_rules],
            "table_rules": [r.to_dict() for r in self.table_rules],
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleSet':
        return cls(
            title_rules=[FormatRule.from_dict(r) for r in data.get("title_rules", [])],
            abstract_rules=[FormatRule.from_dict(r) for r in data.get("abstract_rules", [])],
            keywords_rules=[FormatRule.from_dict(r) for r in data.get("keywords_rules", [])],
            body_rules=[FormatRule.from_dict(r) for r in data.get("body_rules", [])],
            reference_rules=[FormatRule.from_dict(r) for r in data.get("reference_rules", [])],
            figure_rules=[FormatRule.from_dict(r) for r in data.get("figure_rules", [])],
            table_rules=[FormatRule.from_dict(r) for r in data.get("table_rules", [])],
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RuleSet':
        return cls.from_dict(json.loads(json_str))
    
    def get_rules_for_target(self, target: str) -> List[FormatRule]:
        """获取指定目标的规则"""
        mapping = {
            "title": self.title_rules,
            "abstract": self.abstract_rules,
            "keywords": self.keywords_rules,
            "body": self.body_rules,
            "reference": self.reference_rules,
            "figure": self.figure_rules,
            "table": self.table_rules,
        }
        return mapping.get(target, [])
    
    def merge(self, other: 'RuleSet') -> 'RuleSet':
        """合并另一个规则集（后者覆盖前者）"""
        return RuleSet(
            title_rules=self.title_rules + other.title_rules,
            abstract_rules=self.abstract_rules + other.abstract_rules,
            keywords_rules=self.keywords_rules + other.keywords_rules,
            body_rules=self.body_rules + other.body_rules,
            reference_rules=self.reference_rules + other.reference_rules,
            figure_rules=self.figure_rules + other.figure_rules,
            table_rules=self.table_rules + other.table_rules,
        )


class FormatEngine:
    """格式引擎 - 应用规则到文档"""
    
    def __init__(self):
        self.rules: Optional[RuleSet] = None
        
    def load_rules(self, rules: RuleSet):
        """加载规则集"""
        self.rules = rules
        
    def load_rules_from_json(self, json_str: str):
        """从JSON加载规则"""
        self.rules = RuleSet.from_json(json_str)
    
    def get_applied_format(self, target: str) -> Dict[str, Any]:
        """获取应用到指定目标的最终格式"""
        if not self.rules:
            return {}
        
        rules = self.rules.get_rules_for_target(target)
        applied = {}
        
        for rule in rules:
            for key, value in rule.to_dict().items():
                if key != "target" and value is not None:
                    applied[key] = value
        
        return applied
    
    def apply_rules_to_paragraph(self, para_format: Dict[str, Any], target: str) -> Dict[str, Any]:
        """应用规则到段落格式"""
        applied = self.get_applied_format(target)
        return {**para_format, **applied}
    
    def validate_rules(self, rules_json: str) -> tuple[bool, str]:
        """验证规则JSON的有效性"""
        try:
            data = json.loads(rules_json)
            required_fields = ["title_rules", "body_rules"]  # 至少需要标题和正文规则
            for field in required_fields:
                if field not in data:
                    return False, f"缺少必要字段: {field}"
            return True, "规则验证通过"
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误: {str(e)}"
    
    @staticmethod
    def format_rule_to_text(rules: List[FormatRule]) -> str:
        """将规则列表转换为可读文本"""
        if not rules:
            return "无特定规则"
        
        parts = []
        for rule in rules:
            rule_parts = [f"目标: {rule.target}"]
            if rule.font_name:
                rule_parts.append(f"字体: {rule.font_name}")
            if rule.font_size:
                rule_parts.append(f"字号: {rule.font_size}磅")
            if rule.bold is not None:
                rule_parts.append(f"加粗: {'是' if rule.bold else '否'}")
            if rule.italic is not None:
                rule_parts.append(f"斜体: {'是' if rule.italic else '否'}")
            if rule.alignment:
                alignment_map = {"left": "左对齐", "center": "居中", "right": "右对齐", "justify": "两端对齐"}
                rule_parts.append(f"对齐: {alignment_map.get(rule.alignment, rule.alignment)}")
            if rule.line_spacing:
                rule_parts.append(f"行距: {rule.line_spacing}倍")
            if rule.first_line_indent:
                rule_parts.append(f"首行缩进: {rule.first_line_indent}字符")
            if rule.space_before:
                rule_parts.append(f"段前: {rule.space_before}磅")
            if rule.space_after:
                rule_parts.append(f"段后: {rule.space_after}磅")
            parts.append(", ".join(rule_parts))
        
        return "\n".join(parts)


# 默认格式规则（学术论文通用）
DEFAULT_RULES = RuleSet(
    title_rules=[
        FormatRule(
            target="title",
            font_name="宋体",
            font_size=22,
            bold=True,
            alignment="center",
            space_before=0,
            space_after=18
        )
    ],
    abstract_rules=[
        FormatRule(
            target="abstract",
            font_name="宋体",
            font_size=12,
            bold=False,
            alignment="justify",
            line_spacing=1.5,
            first_line_indent=2,
            space_before=0,
            space_after=12
        )
    ],
    keywords_rules=[
        FormatRule(
            target="keywords",
            font_name="宋体",
            font_size=12,
            bold=False,
            alignment="left",
            space_before=6,
            space_after=12
        )
    ],
    body_rules=[
        FormatRule(
            target="body",
            font_name="宋体",
            font_size=12,
            bold=False,
            alignment="justify",
            line_spacing=1.5,
            first_line_indent=2,
            space_before=0,
            space_after=0
        )
    ],
    reference_rules=[
        FormatRule(
            target="reference",
            font_name="宋体",
            font_size=10.5,
            bold=False,
            alignment="left",
            line_spacing=1.5,
            first_line_indent=0,
            space_before=6,
            space_after=6
        )
    ]
)
