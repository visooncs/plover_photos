# Plover Photos (智能 AI 相册)

**Plover Photos** 是一款专为个人和家庭设计的现代化 AI 相册管理系统，旨在提供类似 Google Photos 的流畅体验。它利用先进的深度学习技术实现语义搜索、精准人脸识别和智能回忆功能，并采用前后端分离的现代化架构开发。

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg)

GitHub 仓库: [https://github.com/visooncs/plover_photos](https://github.com/visooncs/plover_photos)

**中文文档** | [English](README_en.md)

## ✨ 主要功能

- **📸 智能扫描**: 自动监控并导入指定目录下的照片和视频（支持 Live Photo）。
- **🔍 语义搜索**: 基于 CLIP 模型，支持通过自然语言描述搜索照片（例如“海边的日落”、“骑自行车的人”）。
- **👤 人脸识别**: 使用 InsightFace 进行高精度人脸检测与识别，支持自动聚类将同一人的照片归类。
- **🎬 视频分析**: 支持从视频文件中提取人脸信息，不仅能识别照片中的人，还能识别视频中的人物。
- **🎞️ 动态照片**: 完美支持 Apple Live Photos 和 Google Motion Photos，在网页端即可播放动态效果。
- **🗺️ 足迹地图**: 自动解析照片 GPS 信息，生成可视化足迹地图，支持按地点聚类查看。
- **📅 智能回忆**: 自动生成“那年今日”等基于时间维度的回忆相册。
- **🔒 隐私优先**: 数据完全本地存储，无需上传云端，确保个人隐私安全。
- **🚀 性能优化**: 针对 RTX 4090 D 等高端显卡进行了深度优化，支持 GPU 加速 AI 推理。
- **🖼️ 现代 UI**: 采用 Vue 3 + Tailwind CSS 构建的响应式界面，支持瀑布流布局、暗色模式和流畅的图片预览。
- **⚡ 后台任务**: 内置强大的异步任务管理系统，支持实时查看扫描和分析进度。
- **🐳 Docker 部署**: 提供完整的一键 Docker 部署方案，包含 PostgreSQL 向量数据库。

<img width="2094" height="1220" alt="image" src="https://github.com/user-attachments/assets/a201dfc3-50ae-4985-92c7-8a05df2f4ac9" />
<img width="2094" height="1220" alt="image" src="https://github.com/user-attachments/assets/57cfceca-304a-4bfd-85da-be2e28e33d5a" />
<img width="2094" height="1220" alt="image" src="https://github.com/user-attachments/assets/0c8ea8fa-d9e8-4cf4-b27b-60edc1d83627" />


## 🛠️ 技术栈

- **后端**: Django 5 + Python 3.12 + Django REST Framework
- **前端**: Vue 3 + Vite + Pinia + Tailwind CSS
- **数据库**: PostgreSQL 16 + pgvector (向量扩展)
- **AI 模型**: CLIP (语义理解), InsightFace (人脸识别)
- **部署**: Docker & Docker Compose

## 🚀 快速开始

### 方式一：Docker 一键部署（推荐）

最简单的方式是使用 Docker 启动整个应用栈（包含数据库、后端和前端）。

1. **进入 Docker 目录**:
   ```bash
   cd docker
   ```

2. **启动服务**:
   ```bash
   # 使用 PowerShell 脚本 (Windows)
   .\deploy.ps1
   
   # 或者直接使用 docker-compose
   docker-compose up -d --build
   ```

3. **访问应用**:
   - **前端页面**: [http://localhost](http://localhost)
   - **后端 API**: [http://localhost:8200/api/](http://localhost:8200/api/)
   - **后台管理**: [http://localhost:8200/admin/](http://localhost:8200/admin/)

> **提示**: 后端服务端口已映射为 **8200**。

### 方式二：本地开发启动

如果您想进行代码开发，可以分别启动前后端。

1. **环境准备**:
   确保已安装 Python 3.12+, Node.js 18+ 和 PostgreSQL (带 pgvector 扩展)。

2. **后端启动**:
   ```bash
   pip install -r backend/requirements.txt
   python backend/manage.py migrate
   python backend/manage.py runserver 8000
   ```

3. **前端启动**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📖 使用指南

### 1. 导入照片
部署成功后，系统会自动挂载 Docker 配置中指定的宿主机路径（默认为 `D:\` 映射到 `/mnt/d`）。
您可以在前端页面的 **系统维护** -> **扫描照片库** 中触发扫描任务。

### 2. AI 功能使用
在 **系统维护** 页面，您可以手动触发以下 AI 任务（建议按顺序执行）：
1. **扫描照片库**: 发现新文件。
2. **人脸识别**: 检测并提取人脸特征。
3. **人脸聚类**: 将相似人脸归类。
4. **生成语义向量**: 为语义搜索提供支持。
5. **生成回忆**: 创建基于日期的回忆集锦。

### 3. 系统更新
如果您获取了最新代码，请运行更新脚本以重新构建镜像：
```bash
cd docker
.\update.ps1
```

## 📂 目录结构

```
plover.store/
├── backend/            # Django 后端源码
├── frontend/           # Vue 3 前端源码
├── docker/             # Docker 部署配置 & 脚本
├── docs/               # 项目文档
├── models/             # AI 模型缓存目录
└── requirements.txt    # Python 依赖列表
```

## 📝 更多文档
详细的使用说明和配置指南，请查阅：
- [部署指南](docs/部署指南.md)
- [用户手册](docs/用户手册.md)
- [接口文档](docs/接口文档.md)

## 📮 联系方式

如果您有任何问题或建议，欢迎联系作者：

- **Email**: visooncs@gmail.com
- **QQ/Email**: 316264262@qq.com
