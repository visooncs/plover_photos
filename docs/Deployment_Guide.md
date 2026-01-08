# Plover Photos Deployment Guide

This guide details how to deploy Plover Photos on your server or local environment.

## 1. Environment Preparation

### Hardware Requirements
- **CPU**: 4 cores or more recommended (required for AI processing)
- **RAM**: 8GB or more recommended (especially when running AI models)
- **GPU (Optional)**: NVIDIA graphics card (supporting CUDA) can significantly accelerate face recognition and semantic analysis.
- **Storage**: SSD recommended for database and thumbnails; HDD can be used for storing original photos.

### Software Requirements
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Operating System**: Windows 11 (WSL2), Linux (Ubuntu 22.04+), macOS

## 2. Docker One-Click Deployment (Recommended)

Docker is the simplest and recommended way to deploy, containing all necessary dependent services (PostgreSQL, Redis, Nginx, etc.).

### Step 1: Get Code
If you haven't got the code yet, please clone the repository:
```bash
git clone https://github.com/visooncs/plover_photos.git
cd plover_photos/docker
```

### Step 2: Start Services

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

**Linux / macOS:**
```bash
docker-compose up -d --build
```

### Step 3: Verify Deployment
After startup is complete, visit the following addresses to check service status:
- **Frontend Page**: `http://localhost`
- **Backend API**: `http://localhost:8200/api/` (Returning 404 or API root is normal)
- **Admin Panel**: `http://localhost:8200/admin/`

## 3. Configuration Instructions

### Environment Variables (.env)
Mainly configured in the `environment` section of `docker-compose.yml`, or use a `.env` file.

- `POSTGRES_PASSWORD`: Database password
- `SECRET_KEY`: Django secret key (must be changed in production)
- `DOCKER_PATH_MAPPINGS`: Host path mapping (Windows specific, used to map D:\ to /mnt/d)

### Storage Mapping
By default, `docker-compose.yml` mounts the following volumes:
- `postgres_data`: Database persistence storage
- `media_volume`: Thumbnails and uploaded files
- `D:\` -> `/mnt/d`: Mounts D drive to container by default for scanning photos. You can modify the `volumes` section in `docker-compose.yml` to mount other paths.

## 4. System Update

When a new version is released, please follow these steps to update:

1. **Pull Latest Code**:
   ```bash
   git pull
   ```

2. **Run Update Script**:
   ```bash
   cd docker
   .\update.ps1
   # Or
   docker-compose up -d --build
   ```
   This will automatically rebuild images and restart containers.

## 5. AI Model Localization

To speed up startup, it is recommended to manually download AI models:

1. **InsightFace (Face Recognition)**:
   - Download [buffalo_l.zip](https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip)
   - Unzip to project root: `./models/insightface/models/buffalo_l/`
   - Ensure it contains `.onnx` files.

2. **CLIP (Semantic Search)**:
   - Models are automatically cached to `./models/huggingface/`.
   - You can download `clip-ViT-B-32` related files from HuggingFace mirror sites and put them in this directory.
