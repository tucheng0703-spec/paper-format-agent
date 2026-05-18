# 📄 论文格式智能体

AI驱动的学术论文格式调整工具，基于 Streamlit + LLM + 规则引擎。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API Key

复制环境变量模板并填入你的硅基流动API Key：

```bash
cp .env.example .env
# 编辑 .env 文件，填入 SILICONFLOW_API_KEY
```

### 3. 启动应用

```bash
streamlit run app.py
```

或使用启动脚本：

```bash
bash start.sh
```

## 📋 功能说明

### 格式模板改版
上传论文 + 粘贴格式要求文本 → 智能解析 → 输出标准格式

适用场景：
- 期刊投稿格式调整
- 会议论文格式规范
- 学位论文格式要求

### 样例参照改版
上传论文 + 上传1-3篇样例论文 → 逆向提取格式 → 智能应用

适用场景：
- 参考他人论文格式
- 模仿目标期刊风格
- 批量处理多篇论文

### 历史记录
- 查看历次任务记录
- 下载历史输出文件
- 统计使用情况

## 📁 项目结构

```
论文格式智能体/
├── app.py              # 主入口
├── config.py           # 配置
├── requirements.txt    # 依赖
├── .env.example        # 环境变量模板
├── start.sh            # 启动脚本
├── utils/
│   ├── docx_parser.py  # Word文档解析
│   ├── docx_writer.py  # Word文档生成
│   ├── format_engine.py # 格式规则引擎
│   ├── llm.py          # LLM调用
│   ├── pdf_parser.py   # PDF解析
│   └── storage.py      # SQLite存储
├── pages/
│   ├── HomePage.py     # 首页
│   ├── TemplateMode.py # 格式模板改版
│   ├── SampleMode.py   # 样例参照改版
│   └── HistoryPage.py  # 历史记录
└── .streamlit/
    └── config.toml     # Streamlit配置
```

## ⚙️ 技术栈

- **前端**: Streamlit
- **Word操作**: python-docx
- **LLM**: 硅基流动 API (Qwen/Qwen2.5-72B-Instruct)
- **PDF解析**: pdfplumber
- **存储**: SQLite

## 📝 使用示例

### 格式模板改版

1. 点击「格式模板改版」
2. 上传待处理的论文 .docx 文件
3. 选择常用模板或自定义输入格式要求
4. 点击「开始改版」
5. 等待处理完成，下载结果

### 样例参照改版

1. 点击「样例参照改版」
2. 上传待处理的论文 .docx 文件
3. 上传1-3篇格式规范的样例论文（支持 .docx 和 .pdf）
4. 点击「开始改版」
5. 等待处理完成，下载结果

## 🔧 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| SILICONFLOW_API_KEY | 硅基流动API Key | 必填 |
| LLM_MODEL | 使用的模型 | Qwen/Qwen2.5-72B-Instruct |

## ⚠️ 注意事项

1. **API Key**: 必须配置有效的硅基流动API Key才能使用
2. **文件格式**: 仅支持 .docx 格式的论文文件
3. **样例论文**: PDF格式的解析可能不够精确，建议优先使用 .docx
4. **内容安全**: 工具仅修改格式，不改变论文的文字内容

## 📄 License

MIT License
