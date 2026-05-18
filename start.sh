#!/bin/bash

# 论文格式智能体启动脚本

echo "📄 论文格式智能体启动中..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version=3.8

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ 需要 Python 3.8 或更高版本，当前版本: $python_version"
    exit 1
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️ .env 文件不存在，正在创建..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑并填入 SILICONFLOW_API_KEY"
fi

# 检查依赖
echo "📦 检查依赖..."
if ! pip show streamlit > /dev/null 2>&1; then
    echo "📥 安装依赖..."
    pip install -r requirements.txt
fi

# 启动应用
echo "🚀 启动 Streamlit 应用..."
streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
