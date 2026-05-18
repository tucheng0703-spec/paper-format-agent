"""
论文格式智能体 - 主入口
"""
import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入页面模块
from pages.HomePage import render_home_page
from pages.TemplateMode import render_template_mode
from pages.SampleMode import render_sample_mode
from pages.HistoryPage import render_history_page


def main():
    """主函数"""
    
    # 页面配置
    st.set_page_config(
        page_title="论文格式智能体",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 初始化session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "HomePage"
    
    # 侧边栏导航
    with st.sidebar:
        st.markdown("### 📄 论文格式智能体")
        st.markdown("---")
        
        # 导航菜单
        menu_items = {
            "HomePage": "🏠 首页",
            "TemplateMode": "📝 格式模板改版",
            "SampleMode": "📚 样例参照改版",
            "HistoryPage": "📜 历史记录"
        }
        
        for page_id, page_label in menu_items.items():
            if page_id == st.session_state.current_page:
                st.markdown(f"**👉 {page_label}**")
            else:
                if st.button(page_label, use_container_width=True, key=f"nav_{page_id}"):
                    st.session_state.current_page = page_id
                    st.rerun()
        
        st.markdown("---")
        
        # 配置信息
        st.markdown("### ⚙️ 配置")
        from config import get_api_key
        api_key = get_api_key()
        if api_key:
            st.success("✅ API Key 已配置")
        else:
            st.error("❌ 请在 Secrets 配置 API Key")
        
        # 链接
        st.markdown("---")
        st.markdown("""
        **使用帮助**:
        1. 配置 `.env` 文件中的 API Key
        2. 上传论文文件
        3. 选择改版模式
        4. 下载格式化后的论文
        """)
    
    # 主内容区
    current_page = st.session_state.current_page
    
    if current_page == "HomePage":
        render_home_page()
    elif current_page == "TemplateMode":
        render_template_mode()
    elif current_page == "SampleMode":
        render_sample_mode()
    elif current_page == "HistoryPage":
        render_history_page()


if __name__ == "__main__":
    main()
