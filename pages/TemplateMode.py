"""
格式模板改版页面
"""
import streamlit as st
import time
from pathlib import Path
from datetime import datetime
import tempfile
import os

from config import OUTPUT_DIR
from utils.docx_parser import DocxParser, extract_docx_format
from utils.format_engine import RuleSet, FormatRule
from utils.docx_writer import apply_rules_to_docx
from utils.llm import get_llm_client
from utils.storage import get_storage


def parse_uploaded_file(uploaded_file) -> str:
    """解析上传的文件，返回临时文件路径"""
    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


def render_template_mode():
    """渲染格式模板改版页面"""
    
    st.markdown("## 📝 格式模板改版")
    st.markdown("上传论文 + 粘贴格式要求 → 智能解析 → 输出标准格式")
    
    # 初始化session state
    if "template_result" not in st.session_state:
        st.session_state.template_result = None
    if "template_rules" not in st.session_state:
        st.session_state.template_rules = None
    if "template_progress" not in st.session_state:
        st.session_state.template_progress = 0
    
    # 文件上传
    st.markdown("### 📤 上传论文")
    uploaded_paper = st.file_uploader(
        "选择论文文件（支持 .docx 格式）",
        type=["docx"],
        help="请上传需要调整格式的论文文件"
    )
    
    if uploaded_paper:
        # 保存到临时文件
        paper_path = parse_uploaded_file(uploaded_paper)
        
        # 显示论文信息
        with st.expander("📄 论文信息", expanded=True):
            try:
                format_info = extract_docx_format(paper_path)
                summary = format_info["summary"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("段落数", summary["total_paragraphs"])
                with col2:
                    st.metric("表格数", summary["total_tables"])
                with col3:
                    sections_str = ", ".join([f"{k}: {v}" for k, v in summary["sections"].items()])
                    st.text(f"章节: {sections_str if sections_str else '未识别'}")
                
                # 预览前500字
                st.text_area(
                    "内容预览",
                    format_info["full_text"][:500] + "..." if len(format_info["full_text"]) > 500 else format_info["full_text"],
                    height=150,
                    disabled=True
                )
            except Exception as e:
                st.error(f"解析论文失败: {str(e)}")
        
        st.markdown("---")
        
        # 格式要求输入
        st.markdown("### 📋 格式要求")
        
        # 常用模板选择
        template_presets = st.selectbox(
            "选择常用格式模板（可选）",
            ["自定义输入", "通用期刊论文", "硕士学位论文", "博士学位论文", "IEEE期刊", "Nature期刊"]
        )
        
        preset_content = {
            "通用期刊论文": """一、论文题目
题目应简明、具体、确切，概括文章的要旨。一般不超过20个汉字。

二、摘要
摘要应客观地反映论文的主要内容，具有独立性和自含性。字数一般为200-300字。

三、关键词
关键词是反映论文主题概念的词或词组，一般每篇3-8个。

四、正文
正文部分使用宋体，小四号字（12磅），1.5倍行距。
首行缩进2字符。
两端对齐。

五、参考文献
参考文献使用宋体，五号字（10.5磅），左对齐，1.5倍行距。""",
            
            "硕士学位论文": """一、论文题目
题目一般不超过25个字，必要时可加副标题。

二、摘要
中文摘要约500字，英文摘要约300词。

三、关键词
3-5个关键词。

四、正文
正文使用宋体，小四号字，1.5倍行距，首行缩进2字符，两端对齐。

五、参考文献
按国家标准GB/T 7714-2015著录。""",
            
            "博士学位论文": """一、论文题目
题目一般不超过25个字，必要时可加副标题。

二、摘要
中文摘要约800字，英文摘要约500词。

三、关键词
5-8个关键词。

四、正文
正文使用宋体，小四号字，1.5倍行距，首行缩进2字符，两端对齐。

五、参考文献
按国家标准GB/T 7714-2015著录。""",
            
            "IEEE期刊": """1. Title: Times New Roman, 14pt, Bold, Center aligned
2. Abstract: 150-200 words, single column
3. Index Terms: up to 5 keywords
4. Body Text: Times New Roman, 10pt, single column, two-column format
5. References: Numbered sequentially, 9pt""",
            
            "Nature期刊": """1. Title: Arial, 18pt, Bold
2. Authors and affiliations
3. Abstract: 150 words maximum
4. Main text: Arial, 12pt, 1.5 line spacing
5. References: Numbered in order of appearance"""
        }
        
        if template_presets != "自定义输入":
            default_text = preset_content.get(template_presets, "")
        else:
            default_text = ""
        
        format_requirements = st.text_area(
            "粘贴格式要求文本",
            value=default_text,
            height=300,
            placeholder="请粘贴目标期刊或学校的格式要求，例如：\n- 题目：黑体，三号字，居中对齐\n- 摘要：宋体，五号字，首行缩进2字符\n- 正文：宋体，小四号，1.5倍行距..."
        )
        
        st.markdown("---")
        
        # 操作按钮
        col_start, col_clear = st.columns([1, 1])
        
        with col_start:
            start_button = st.button("🚀 开始改版", type="primary", use_container_width=True)
        
        with col_clear:
            if st.button("🗑️ 清除", use_container_width=True):
                st.session_state.template_result = None
                st.session_state.template_rules = None
                st.session_state.template_progress = 0
                st.rerun()
        
        # 执行改版
        if start_button and uploaded_paper and format_requirements:
            if not format_requirements.strip():
                st.warning("请输入格式要求")
                return
            
            # 检查API Key
            from config import SILICONFLOW_API_KEY
            if not SILICONFLOW_API_KEY:
                st.error("请先在 .env 文件中配置 SILICONFLOW_API_KEY")
                return
            
            # 创建任务记录
            storage = get_storage()
            task_id = storage.create_task(
                task_type="template",
                input_file=uploaded_paper.name
            )
            
            # 进度条
            progress_bar = st.progress(0, text="准备中...")
            
            try:
                # 步骤1: LLM解析格式要求
                progress_bar.progress(10, text="🤖 LLM正在解析格式要求...")
                
                llm_client = get_llm_client()
                rules_data = llm_client.extract_rules_from_requirements(format_requirements)
                
                st.session_state.template_rules = rules_data
                progress_bar.progress(40, text="✅ 格式规则提取完成")
                
                # 显示提取的规则
                with st.expander("📋 提取的格式规则", expanded=False):
                    st.json(rules_data)
                
                # 步骤2: 应用规则
                progress_bar.progress(50, text="⚙️ 正在应用格式规则...")
                
                # 生成输出文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"formatted_{timestamp}.docx"
                output_path = OUTPUT_DIR / output_filename
                
                # 创建规则集
                rules = RuleSet.from_dict(rules_data)
                
                # 应用规则
                result = apply_rules_to_docx(paper_path, str(output_path), rules)
                
                progress_bar.progress(80, text="✅ 格式应用完成")
                
                # 步骤3: 完成
                progress_bar.progress(100, text="🎉 改版完成！")
                
                st.session_state.template_result = {
                    "output_path": str(output_path),
                    "output_filename": output_filename,
                    "total_paragraphs": result["total_paragraphs"],
                    "rules_applied": result["applied_rules"]
                }
                
                # 更新任务状态
                storage.update_task(
                    task_id,
                    output_file=output_filename,
                    rules_applied=rules_data,
                    status="success"
                )
                
                time.sleep(0.5)
                progress_bar.empty()
                
                # 显示结果
                st.success("✅ 格式改版完成！")
                
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ 改版失败: {str(e)}")
                storage.update_task(task_id, status="failed", error_message=str(e))
                import traceback
                st.code(traceback.format_exc())
    
    # 显示结果
    if st.session_state.template_result:
        st.markdown("---")
        st.markdown("### ✅ 改版结果")
        
        result = st.session_state.template_result
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("处理段落数", result["total_paragraphs"])
        with col2:
            st.metric("生成时间", datetime.now().strftime("%H:%M:%S"))
        
        # 下载按钮
        with open(result["output_path"], "rb") as f:
            st.download_button(
                label="📥 下载格式化后的论文",
                data=f,
                file_name=result["output_filename"],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )
        
        # 显示应用的规则
        if st.session_state.template_rules:
            with st.expander("📋 应用的格式规则详情"):
                rules = st.session_state.template_rules
                
                for section in ["title_rules", "abstract_rules", "keywords_rules", "body_rules", "reference_rules"]:
                    section_name = section.replace("_rules", "").title()
                    if rules.get(section):
                        st.markdown(f"**{section_name}**")
                        for rule in rules[section]:
                            rule_text = []
                            if rule.get("font_name"):
                                rule_text.append(f"字体: {rule['font_name']}")
                            if rule.get("font_size"):
                                rule_text.append(f"字号: {rule['font_size']}磅")
                            if rule.get("bold") is not None:
                                rule_text.append(f"加粗: {'是' if rule['bold'] else '否'}")
                            if rule.get("alignment"):
                                rule_text.append(f"对齐: {rule['alignment']}")
                            if rule.get("line_spacing"):
                                rule_text.append(f"行距: {rule['line_spacing']}倍")
                            if rule.get("first_line_indent"):
                                rule_text.append(f"首行缩进: {rule['first_line_indent']}字符")
                            if rule_text:
                                st.markdown(f"- {' | '.join(rule_text)}")
                        st.markdown("")


if __name__ == "__main__":
    render_template_mode()
