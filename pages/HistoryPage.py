"""
历史记录页面
"""
import streamlit as st
from datetime import datetime

from utils.storage import get_storage


def render_history_page():
    """渲染历史记录页面"""
    
    st.markdown("## 📜 历史记录")
    st.markdown("查看历次格式改版任务的记录")
    
    storage = get_storage()
    
    # 统计信息
    stats = storage.get_statistics()
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric("总任务数", stats["total"])
    with stat_col2:
        st.metric("成功完成", stats["success"])
    with stat_col3:
        st.metric("失败任务", stats["failed"])
    with stat_col4:
        st.metric("成功率", stats["success_rate"])
    
    st.markdown("---")
    
    # 分页设置
    page_size = 10
    page_num = st.number_input("页码", min_value=1, value=1, step=1)
    offset = (page_num - 1) * page_size
    
    # 获取任务列表
    tasks = storage.list_tasks(limit=page_size, offset=offset)
    
    if not tasks:
        st.info("暂无历史记录")
        return
    
    # 显示任务列表
    st.markdown(f"### 任务列表 (第 {page_num} 页)")
    
    for task in tasks:
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
            
            with col1:
                # 任务类型
                task_type_map = {
                    "template": "📝 模板改版",
                    "sample": "📚 样例改版"
                }
                task_type_label = task_type_map.get(task["task_type"], task["task_type"])
                st.markdown(f"**{task_type_label}**")
                st.caption(f"ID: {task['id']}")
            
            with col2:
                # 文件名
                input_file = task.get("input_file", "未知")
                output_file = task.get("output_file")
                
                st.text(f"输入: {input_file}")
                if output_file:
                    st.text(f"输出: {output_file}")
            
            with col3:
                # 状态
                status = task.get("status", "pending")
                status_map = {
                    "success": ("✅ 成功", "success"),
                    "failed": ("❌ 失败", "error"),
                    "pending": ("⏳ 处理中", "warning")
                }
                status_label, status_type = status_map.get(status, (status, "info"))
                st.markdown(status_label)
                
                # 时间
                created_at = task.get("created_at")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at)
                        st.caption(dt.strftime("%m-%d %H:%M"))
                    except:
                        pass
            
            with col4:
                # 操作按钮
                if task.get("output_file"):
                    output_path = storage.db_path.replace("paper_formatter.db", f"output/{output_file}")
                    try:
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="下载",
                                data=f,
                                file_name=output_file,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"download_{task['id']}"
                            )
                    except FileNotFoundError:
                        st.caption("文件不存在")
                
                # 删除按钮
                if st.button("🗑️", key=f"delete_{task['id']}", help="删除记录"):
                    storage.delete_task(task["id"])
                    st.rerun()
            
            # 显示错误信息
            if task.get("error_message"):
                with st.expander("查看错误信息"):
                    st.code(task["error_message"])
            
            # 显示应用的规则
            rules_applied = task.get("rules_applied")
            if rules_applied:
                with st.expander("查看应用的规则"):
                    st.json(rules_applied)
            
            st.divider()
    
    # 批量操作
    st.markdown("---")
    col_clear_all, col_export = st.columns([1, 1])
    
    with col_clear_all:
        if st.button("🗑️ 清空所有记录", type="secondary"):
            st.warning("确定要清空所有历史记录吗？此操作不可恢复。")
            if st.button("确认清空", type="primary"):
                # 清空逻辑（逐个删除）
                all_tasks = storage.list_tasks(limit=1000)
                for t in all_tasks:
                    storage.delete_task(t["id"])
                st.success("已清空所有记录")
                st.rerun()
    
    with col_export:
        if st.button("📊 导出统计报告", type="secondary"):
            st.info("统计报告功能开发中...")


if __name__ == "__main__":
    render_history_page()
