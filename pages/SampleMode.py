"""
样例参照改版页面
"""
import streamlit as st
import time
from pathlib import Path
from datetime import datetime
import tempfile

from config import OUTPUT_DIR, SUPPORTED_ALL
from utils.docx_parser import DocxParser, extract_docx_format
from utils.pdf_parser import PDFParser, extract_pdf_format
from utils.format_engine import RuleSet
from utils.docx_writer import apply_rules_to_docx
from utils.llm import get_llm_client
from utils.storage import get_storage


def parse_uploaded_file(uploaded_file) -> tuple:
    """解析上传的文件，返回(文件路径, 文件类型)"""
    suffix = Path(uploaded_file.name).suffix.lower().replace(".", "")
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name, suffix


def extract_sample_format(uploaded_files) -> dict:
    """从多个样例文件中提取格式信息"""
    all_format_info = {
        "title": [],
        "abstract": [],
        "keywords": [],
        "body": [],
        "reference": []
    }
    
    for uploaded_file in uploaded_files:
        file_path, file_type = parse_uploaded_file(uploaded_file)
        
        try:
            if file_type == "docx":
                format_info = extract_docx_format(file_path)
                structure = format_info["structure"]
                
                # 按章节分类
                for section, indices in structure.section_mapping.items():
                    for idx in indices:
                        para = structure.paragraphs[idx]
                        para_dict = {
                            "text": para.text,
                            "style_name": para.style_name,
                            "font_name": para.font_name,
                            "font_size": para.font_size,
                            "bold": para.bold,
                            "italic": para.italic,
                            "alignment": para.alignment,
                            "line_spacing": para.line_spacing,
                            "first_line_indent": para.first_line_indent,
                            "space_before": para.space_before,
                            "space_after": para.space_after
                        }
                        if section in all_format_info:
                            all_format_info[section].append(para_dict)
                            
            elif file_type == "pdf":
                pdf_info = extract_pdf_format(file_path)
                # PDF格式信息较简略，放入body
                all_format_info["body"].append({
                    "text": pdf_info["full_text"][:500],
                    "font_size": 12,
                    "line_spacing": 1.5
                })
                
        except Exception as e:
            st.warning(f"解析 {uploaded_file.name} 时出错: {str(e)}")
    
    return all_format_info


def render_sample_mode():
    """渲染样例参照改版页面"""
    
    st.markdown("## 📚 样例参照改版")
    st.markdown("上传论文 + 上传1-3篇样例论文 → 逆向提取格式 → 智能应用到目标论文")
    
    # 初始化session state
    if "sample_result" not in st.session_state:
        st.session_state.sample_result = None
    if "sample_rules" not in st.session_state:
        st.session_state.sample_rules = None
    
    # 文件上传区域
    st.markdown("### 📤 上传文件")
    
    col_paper, col_samples = st.columns(2)
    
    with col_paper:
        st.markdown("**📄 待处理论文**")
        uploaded_paper = st.file_uploader(
            "选择需要调整格式的论文",
            type=["docx"],
            key="sample_paper",
            help="支持 .docx 格式"
        )
    
    with col_samples:
        st.markdown("**📚 样例论文（1-3篇）**")
        uploaded_samples = st.file_uploader(
            "选择样例论文作为格式参照",
            type=["docx", "pdf"],
            accept_multiple_files=True,
            key="sample_files",
            help="支持 .docx 和 .pdf 格式，将从样例中逆向提取格式规则"
        )
    
    # 文件验证
    if uploaded_paper and len(uploaded_samples) > 3:
        st.error("样例论文最多上传3篇")
        return
    
    # 显示上传的文件信息
    if uploaded_paper:
        st.markdown("---")
        st.markdown("### 📋 上传文件预览")
        
        preview_col1, preview_col2 = st.columns(2)
        
        with preview_col1:
            st.markdown("**待处理论文**")
            st.info(f"📄 {uploaded_paper.name}")
            
            # 解析论文内容
            paper_path, _ = parse_uploaded_file(uploaded_paper)
            try:
                format_info = extract_docx_format(paper_path)
                summary = format_info["summary"]
                st.caption(f"段落数: {summary['total_paragraphs']}")
                
                # 内容预览
                with st.expander("内容预览"):
                    st.text(format_info["full_text"][:300] + "...")
            except Exception as e:
                st.error(f"解析失败: {str(e)}")
        
        if uploaded_samples:
            with preview_col2:
                st.markdown("**样例论文**")
                for i, sample in enumerate(uploaded_samples, 1):
                    st.info(f"📚 {i}. {sample.name}")
        
        st.markdown("---")
        
        # 操作按钮
        col_start, col_clear = st.columns([1, 1])
        
        with col_start:
            start_button = st.button("🚀 开始改版", type="primary", use_container_width=True)
        
        with col_clear:
            if st.button("🗑️ 清除", use_container_width=True):
                st.session_state.sample_result = None
                st.session_state.sample_rules = None
                st.rerun()
        
        # 执行改版
        if start_button and uploaded_paper and uploaded_samples:
            if not uploaded_samples:
                st.warning("请上传至少1篇样例论文")
                return
            
            # 检查API Key
            from config import SILICONFLOW_API_KEY
            if not SILICONFLOW_API_KEY:
                st.error("请先在 .env 文件中配置 SILICONFLOW_API_KEY")
                return
            
            # 创建任务记录
            storage = get_storage()
            task_id = storage.create_task(
                task_type="sample",
                input_file=uploaded_paper.name
            )
            
            # 进度条
            progress_bar = st.progress(0, text="准备中...")
            
            try:
                # 步骤1: 解析待处理论文
                progress_bar.progress(5, text="📄 正在解析待处理论文...")
                paper_path, _ = parse_uploaded_file(uploaded_paper)
                
                # 步骤2: 提取样例论文格式
                progress_bar.progress(15, text="📚 正在提取样例论文格式...")
                sample_info = extract_sample_format(uploaded_samples)
                
                # 统计各部分数量
                section_counts = {k: len(v) for k, v in sample_info.items()}
                st.caption(f"样例格式统计: {section_counts}")
                
                # 步骤3: LLM逆向提取规则
                progress_bar.progress(25, text="🤖 LLM正在逆向提取格式规则...")
                
                llm_client = get_llm_client()
                rules_data = llm_client.extract_rules_from_sample(sample_info)
                
                st.session_state.sample_rules = rules_data
                progress_bar.progress(50, text="✅ 格式规则提取完成")
                
                # 显示提取的规则
                with st.expander("📋 从样例提取的格式规则", expanded=False):
                    st.json(rules_data)
                
                # 步骤4: 应用规则到论文
                progress_bar.progress(55, text="⚙️ 正在应用格式规则...")
                
                # 生成输出文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"formatted_from_sample_{timestamp}.docx"
                output_path = OUTPUT_DIR / output_filename
                
                # 创建规则集
                rules = RuleSet.from_dict(rules_data)
                
                # 应用规则
                result = apply_rules_to_docx(paper_path, str(output_path), rules)
                
                progress_bar.progress(85, text="✅ 格式应用完成")
                
                # 步骤5: 完成
                progress_bar.progress(100, text="🎉 改版完成！")
                
                st.session_state.sample_result = {
                    "output_path": str(output_path),
                    "output_filename": output_filename,
                    "total_paragraphs": result["total_paragraphs"],
                    "rules_applied": result["applied_rules"],
                    "sample_count": len(uploaded_samples)
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
    if st.session_state.sample_result:
        st.markdown("---")
        st.markdown("### ✅ 改版结果")
        
        result = st.session_state.sample_result
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("处理段落数", result["total_paragraphs"])
        with col2:
            st.metric("样例论文数", result["sample_count"])
        with col3:
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
        if st.session_state.sample_rules:
            with st.expander("📋 应用的格式规则详情"):
                rules = st.session_state.sample_rules
                
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
    
    # 使用说明
    if not uploaded_paper:
        st.markdown("---")
        st.markdown("### 📖 使用说明")
        
        with st.expander("如何准备样例论文？", expanded=True):
            st.markdown("""
            1. **选择格式规范的论文**：选择与你目标期刊或学校格式一致的论文
            2. **优先选择同期刊论文**：最好选择目标期刊近期发表的论文
            3. **DOCX格式更准确**：Word格式的解析更精确，PDF可能会有部分格式丢失
            
            **上传数量建议**：
            - 上传1篇：适合单一格式目标
            - 上传2-3篇：可以综合多篇论文的格式特点
            """)
        
        with st.expander("样例参照 vs 格式模板，如何选择？", expanded=True):
            st.markdown("""
            | 模式 | 适用场景 | 优点 |
            |------|---------|------|
            | **格式模板** | 有明确格式要求文档 | 规则精确，不受样例限制 |
            | **样例参照** | 参考他人论文格式 | 更灵活，可模仿复杂格式 |
            
            **建议**：
            - 如果你有格式要求文本（如期刊官网的投稿指南），使用**格式模板**
            - 如果你想模仿某篇论文的格式，使用**样例参照**
            """)


if __name__ == "__main__":
    render_sample_mode()
