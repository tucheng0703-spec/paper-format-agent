"""
首页
"""
import streamlit as st
from datetime import datetime


def render_home_page():
    """渲染首页"""
    
    # Hero区域
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 2.5rem; color: #2E86AB; margin-bottom: 0.5rem;">
            📄 论文格式智能体
        </h1>
        <p style="font-size: 1.2rem; color: #666;">
            AI驱动的学术论文格式调整工具
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 功能介绍
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 格式模板改版
        上传论文 + 粘贴格式要求文本 → 智能解析 → 输出标准格式
        
        **适用场景：**
        - 期刊投稿格式调整
        - 会议论文格式规范
        - 学位论文格式要求
        """)
        
        st.markdown("""
        ### 🔍 格式差异对比
        高亮标注修改处，直观对比改版前后差异
        
        **功能特点：**
        - 颜色标记改动位置
        - 详细的修改报告
        - 支持撤销重做
        """)
    
    with col2:
        st.markdown("""
        ### 📚 样例参照改版
        上传论文 + 上传样例论文 → 逆向提取格式 → 智能应用
        
        **适用场景：**
        - 参考他人论文格式
        - 模仿目标期刊风格
        - 批量处理多篇论文
        """)
        
        st.markdown("""
        ### ✨ 核心优势
        
        - 🤖 **AI智能理解** - LLM精准解析格式要求
        - 📐 **精确格式控制** - 规则引擎确保格式无误
        - 🔒 **内容安全** - 仅修改格式，不改变文字内容
        - 📊 **全程可追溯** - 历史记录完整保存
        """)
    
    st.divider()
    
    # 使用统计
    try:
        from utils.storage import get_storage
        stats = get_storage().get_statistics()
        
        st.markdown("### 📈 使用统计")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("总任务数", stats["total"])
        with stat_col2:
            st.metric("成功完成", stats["success"])
        with stat_col3:
            st.metric("失败任务", stats["failed"])
        with stat_col4:
            st.metric("成功率", stats["success_rate"])
    except Exception as e:
        pass
    
    st.divider()
    
    # 快速开始
    st.markdown("### 🚀 快速开始")
    
    quick_col1, quick_col2 = st.columns(2)
    
    with quick_col1:
        if st.button("📝 格式模板改版", use_container_width=True, type="primary"):
            st.session_state.current_page = "TemplateMode"
            st.rerun()
    
    with quick_col2:
        if st.button("📚 样例参照改版", use_container_width=True, type="primary"):
            st.session_state.current_page = "SampleMode"
            st.rerun()
    
    st.divider()
    
    # 底部信息
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.85rem; padding: 1rem 0;">
        <p>© 2024 论文格式智能体 · 基于 Streamlit + LLM + 规则引擎</p>
        <p>支持 Word (.docx) 文档格式调整</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render_home_page()
