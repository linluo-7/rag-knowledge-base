# Python 环境准备

本项目使用 Python 3.10+ 作为后端开发语言，推荐使用 Conda 管理 Python 环境。

---

## 1. 检查 Python 版本

```bash
python3 --version
```

**预期输出：**
```
Python 3.10.x 或更高
```

如果版本过低或未安装，参考下一节安装 Python。

---

## 2. 安装 Conda（推荐）

Conda 可以管理多个 Python 环境，避免包冲突。

### 2.1 下载 Miniconda

```bash
cd /tmp
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

### 2.2 安装 Miniconda

```bash
bash Miniconda3-latest-Linux-x86_64.sh
```

**安装过程：**
```
Welcome to Miniconda3-latest-Linux-x86_64.sh

按 Enter 继续...
按 q 跳过 License，直接 Accept
输入 yes 确认安装路径（默认即可）
输入 yes 初始化 Conda
```

### 2.3 重新加载 Shell 配置

```bash
# 如果使用的是 bash
source ~/.bashrc

# 如果使用的是 zsh
source ~/.zshrc
```

### 2.4 验证安装

```bash
conda --version
```

**预期输出：**
```
conda 23.x.x
```

---

## 3. 创建项目环境

### 3.1 创建 Python 3.10 环境

```bash
conda create -n rag python=3.10 -y
```

### 3.2 激活环境

```bash
conda activate rag
```

**激活后终端会显示：**
```
(rag) user@hostname:~/rag-knowledge-base$
```

### 3.3 验证 Python 版本

```bash
python --version
```

**预期输出：**
```
Python 3.10.x
```

---

## 4. 安装基础依赖

### 4.1 升级 pip

```bash
pip install --upgrade pip
```

### 4.2 安装 PyTorch（CPU 版本）

PyTorch 是深度学习的基础库，BGE Embedding 模型需要它。

```bash
pip install torch torchvision torchaudio
```

**如果服务器有 NVIDIA GPU**，安装 GPU 版本：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4.3 安装 LangChain

```bash
pip install langchain langchain-community
```

### 4.4 安装向量数据库和图数据库 SDK

```bash
pip install pymilvus neo4j
```

### 4.5 安装 Embedding 模型

```bash
pip install sentence-transformers
```

### 4.6 安装 FastAPI 和 Web 服务

```bash
pip install fastapi uvicorn python-multipart
```

### 4.7 安装文档解析库

```bash
pip install python-docx
```

### 4.8 安装 MiniMax SDK

```bash
pip install minimaxai
```

如果没有合适的 SDK，也可以直接用 HTTP 请求调用 MiniMax API。

### 4.9 安装其他工具库

```bash
pip install pydantic python-dotenv requests
```

---

## 5. 一键安装所有依赖

为了方便，可以创建 `requirements.txt`：

```bash
cd ~/rag-knowledge-base/backend
```

创建 `requirements.txt`：

```
# Web 框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# LangChain
langchain==0.1.4
langchain-community==0.0.17

# 向量数据库
pymilvus==2.3.3

# 图数据库
neo4j==5.19.0

# Embedding
sentence-transformers==2.3.1

# PyTorch
torch==2.1.2
torchvision==0.16.2
torchaudio==2.1.2

# 文档解析
python-docx==1.1.0

# LLM API
requests==2.31.0

# 数据处理
pydantic==2.5.3
python-dotenv==1.0.0
numpy==1.26.3

# 异步处理
aiohttp==3.9.1
```

然后执行一键安装：

```bash
pip install -r requirements.txt
```

---

## 6. 验证安装

创建 `check_env.py`：

```python
import sys
print(f"Python: {sys.version}")

# 检查各库是否安装成功
try:
    import torch
    print(f"PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"PyTorch: 未安装 - {e}")

try:
    import langchain
    print(f"LangChain: {langchain.__version__}")
except ImportError as e:
    print(f"LangChain: 未安装 - {e}")

try:
    import pymilvus
    print(f"PyMilvus: {pymilvus.__version__}")
except ImportError as e:
    print(f"PyMilvus: 未安装 - {e}")

try:
    import neo4j
    print(f"Neo4j: {neo4j.__version__}")
except ImportError as e:
    print(f"Neo4j: 未安装 - {e}")

try:
    import sentence_transformers
    print(f"sentence-transformers: {sentence_transformers.__version__}")
except ImportError as e:
    print(f"sentence-transformers: 未安装 - {e}")

try:
    import fastapi
    print(f"FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"FastAPI: 未安装 - {e}")

try:
    import docx
    print(f"python-docx: {docx.__version__}")
except ImportError as e:
    print(f"python-docx: 未安装 - {e}")

print("\n环境检查完成！")
```

运行：

```bash
python check_env.py
```

**预期输出（所有库都显示版本号，无错误）：**
```
Python: 3.10.x
PyTorch: 2.1.2
LangChain: 0.1.4
PyMilvus: 2.3.3
Neo4j: 5.19.0
sentence-transformers: 2.3.1
FastAPI: 0.109.0
python-docx: 0.8.11

环境检查完成！
```

---

## 7. Conda 常用命令

```bash
# 激活环境
conda activate rag

# 退出环境
conda deactivate

# 列出所有环境
conda env list

# 删除环境
conda env remove -n rag

# 导出环境配置
conda env export > environment.yml

# 从配置文件创建环境
conda env create -f environment.yml
```

---

## 8. 虚拟环境管理（可选）

如果不使用 Conda，也可以使用 Python 内置的 venv：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

---

## 9. 配置环境变量

创建 `.env` 文件存储敏感配置：

```bash
cd ~/rag-knowledge-base/backend
touch .env
```

编辑 `.env`：

```env
# MiniMax API 配置
MINIMAX_API_KEY=your_api_key_here
MINIMAX_BASE_URL=https://api.minimax.chat/v

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123456

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 服务配置
API_HOST=0.0.0.0
API_PORT=8000
```

> **注意：** `.env` 文件不要提交到 Git，需要加入 `.gitignore`

---

## 10. 下一个章节

Python 环境准备完成！下一章我们将进行 **项目初始化**。
