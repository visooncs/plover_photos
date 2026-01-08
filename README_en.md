# Plover Photos (Smart AI Photo Gallery)

**Plover Photos** is a modern AI photo management system designed for individuals and families, aiming to provide a smooth experience similar to Google Photos. It leverages advanced deep learning technologies to achieve semantic search, precise face recognition, and smart memory generation, built with a modern architecture separating frontend and backend.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg)

GitHub Repository: [https://github.com/visooncs/plover_photos](https://github.com/visooncs/plover_photos)

[中文文档](README.md) | **English**

## ✨ Key Features

- **📸 Smart Scan**: Automatically monitors and imports photos and videos from specified directories (Live Photo supported).
- **🔍 Semantic Search**: Based on the CLIP model, allowing you to search for photos using natural language descriptions (e.g., "sunset by the sea", "person riding a bike").
- **👤 Face Recognition**: Uses InsightFace for high-precision face detection and recognition, supporting automatic clustering to group photos of the same person.
- **🎬 Video Analysis**: Supports extracting face information from video files, recognizing people not only in photos but also in videos.
- **🎞️ Dynamic Photos**: Full support for Apple Live Photos and Google Motion Photos, allowing playback of dynamic effects directly on the web.
- **🗺️ Footprint Map**: Automatically parses photo GPS information to generate a visualized footprint map, supporting clustered viewing by location.
- **📅 Smart Memories**: Automatically generates memory albums based on time dimensions like "On This Day".
- **🔒 Privacy First**: All data is stored locally, with no upload to the cloud, ensuring personal privacy security.
- **🚀 Performance Optimization**: Deeply optimized for high-end graphics cards like RTX 4090 D, supporting GPU-accelerated AI inference.
- **🖼️ Modern UI**: Responsive interface built with Vue 3 + Tailwind CSS, supporting waterfall layout, dark mode, and smooth image preview.
- **⚡ Background Tasks**: Built-in powerful asynchronous task management system, supporting real-time viewing of scan and analysis progress.
- **🐳 Docker Deployment**: Provides a complete one-click Docker deployment solution, including PostgreSQL vector database.


<img width="2094" height="1220" alt="image" src="https://github.com/user-attachments/assets/a201dfc3-50ae-4985-92c7-8a05df2f4ac9" />
<img width="2094" height="1220" alt="image" src="https://github.com/user-attachments/assets/57cfceca-304a-4bfd-85da-be2e28e33d5a" />
<img width="2094" height="1220" alt="image" src="https://github.com/user-attachments/assets/0c8ea8fa-d9e8-4cf4-b27b-60edc1d83627" />

## 🛠️ Tech Stack

- **Backend**: Django 5 + Python 3.12 + Django REST Framework
- **Frontend**: Vue 3 + Vite + Pinia + Tailwind CSS
- **Database**: PostgreSQL 16 + pgvector (vector extension)
- **AI Models**: CLIP (Semantic Understanding), InsightFace (Face Recognition)
- **Deployment**: Docker & Docker Compose

## 🚀 Quick Start

### Method 1: Docker One-Click Deployment (Recommended)

The simplest way is to use Docker to launch the entire application stack (including database, backend, and frontend).

1. **Enter Docker Directory**:
   ```bash
   cd docker
   ```

2. **Start Services**:
   ```bash
   # Use PowerShell Script (Windows)
   .\deploy.ps1
   
   # Or use docker-compose directly
   docker-compose up -d --build
   ```

3. **Access Application**:
   - **Frontend Page**: [http://localhost](http://localhost)
   - **Backend API**: [http://localhost:8200/api/](http://localhost:8200/api/)
   - **Admin Panel**: [http://localhost:8200/admin/](http://localhost:8200/admin/)

> **Tip**: The backend service port is mapped to **8200**.

### Method 2: Local Development Startup

If you want to develop the code, you can start the frontend and backend separately.

1. **Environment Preparation**:
   Ensure Python 3.12+, Node.js 18+, and PostgreSQL (with pgvector extension) are installed.

2. **Backend Startup**:
   ```bash
   pip install -r backend/requirements.txt
   python backend/manage.py migrate
   python backend/manage.py runserver 8000
   ```

3. **Frontend Startup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📖 User Guide

### 1. Import Photos
After successful deployment, the system automatically mounts the host path specified in the Docker configuration (default is `D:\` mapped to `/mnt/d`).
You can trigger the scan task in **System Maintenance** -> **Scan Photo Library** on the frontend page.

### 2. AI Features Usage
In the **System Maintenance** page, you can manually trigger the following AI tasks (recommended order):
1. **Scan Photo Library**: Discover new files.
2. **Face Recognition**: Detect and extract face features.
3. **Face Clustering**: Group similar faces.
4. **Generate Semantic Vectors**: Support semantic search.
5. **Generate Memories**: Create date-based memory collections.

### 3. System Update
If you have obtained the latest code, please run the update script to rebuild the images:
```bash
cd docker
.\update.ps1
```

## 📂 Directory Structure

```
plover.store/
├── backend/            # Django Backend Source
├── frontend/           # Vue 3 Frontend Source
├── docker/             # Docker Deployment Config & Scripts
├── docs/               # Project Documentation
├── models/             # AI Model Cache Directory
└── requirements.txt    # Python Dependencies List
```

## 📝 More Documentation
For detailed usage instructions and configuration guides, please refer to:
- [Deployment Guide](docs/Deployment_Guide.md)
- [User Guide](docs/User_Guide.md)
- [API Reference](docs/API_Reference.md)

## 📮 Contact

If you have any questions or suggestions, please feel free to contact the author:

- **Email**: visooncs@gmail.com
- **QQ/Email**: 316264262@qq.com
