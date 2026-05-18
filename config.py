"""
论文格式智能体 - 配置文件
"""
import os
from pathlib import Path

# 尝试加载dotenv（本地开发环境）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_api_key():
    """获取API Key，兼容本地.env和Streamlit Cloud secrets"""
    # 优先从Streamlit secrets读取（云端部署）
    try:
        import streamlit as st
        return st.secrets["SILICONFLOW_API_KEY"]
    except:
        pass
    # 其次从环境变量读取
    return os.getenv("SILICONFLOW_API_KEY", "")


# 项目根目录
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# LLM配置
SILICONFLOW_API_KEY = get_api_key()
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
LLM_MODEL = "Qwen/Qwen2.5-72B-Instruct"

# 数据库配置
DB_PATH = BASE_DIR / "paper_formatter.db"

# 支持的文件格式
SUPPORTED_DOCX = ["docx"]
SUPPORTED_PDF = ["pdf"]
SUPPORTED_ALL = SUPPORTED_DOCX + SUPPORTED_PDF

# 段落识别关键词
SECTION_KEYWORDS = {
    "title": ["题目", "标题", "title"],
    "abstract": ["摘要", "abstract"],
    "keywords": ["关键词", "关键字", "keywords", "key words"],
    "introduction": ["引言", "前言", "背景", "introduction"],
    "body": [],  # 正文部分
    "reference": ["参考文献", "reference", "引用"],
    "acknowledgment": ["致谢", "acknowledgment", "acknowledgements"],
    "appendix": ["附录", "appendix"],
}

# 字体映射（中文优先）
FONT_MAPPING = {
    "宋体": "SimSun",
    "仿宋": "FangSong",
    "黑体": "SimHei",
    "楷体": "KaiTi",
    "微软雅黑": "Microsoft YaHei",
    "Times New Roman": "Times New Roman",
    "Arial": "Arial",
}
