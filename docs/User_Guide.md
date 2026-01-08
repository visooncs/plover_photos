# Plover Photos User Guide

Welcome to Plover Photos! This document will guide you on how to use the core features of the system to manage and enjoy your photo library.

## 1. Quick Start

### Access System
Open your browser and visit `http://localhost` (or your server's IP address).

### Interface Overview
- **Timeline**: Home page displays all photos by default, sorted by capture time in reverse chronological order.
- **Library**: Contains categories like "People", "Places", "Recently Added", etc.
- **Map**: View your footprints on the map.
- **Maintenance**: Manage background tasks, import photos, and view system status.

## 2. Import Photos

Plover Photos does not move or modify your original files; it indexes them via "Scanning".

1. Go to **System Maintenance** page.
2. Find **Scan Photo Library** task.
3. Click **Run**.
4. The system will scan all paths mounted in the Docker configuration (e.g., `/mnt/d/Photos`).
   > **Note**: Please ensure your photo folders are mounted into the Docker container.

## 3. AI Smart Features

The system has built-in AI capabilities. It is recommended to perform initialization in the following order:

### 3.1 Face Recognition
- **Function**: Automatically recognizes faces in photos and clusters photos of the same person.
- **Operation**: Click **Face Recognition** -> **Run** on the System Maintenance page.
- **View**: After completion, view results in **Library** -> **People**. You can name people here.

### 3.2 Semantic Search
- **Function**: Allows you to search for photos using natural language.
- **Operation**: Click **Generate Semantic Vectors** -> **Run**.
- **Usage**: Enter descriptions in the top search bar, such as:
  - "Sunset by the sea"
  - "Child in red clothes"
  - "Snow mountain"
  - "Birthday cake"

### 3.3 Smart Memories
- **Function**: Generates themed memories like "On This Day".
- **Operation**: Click **Generate Memories** -> **Run**.
- **View**: Memory cards will appear at the top of the home page or in the sidebar.

## 4. Browse & Manage

### View Details
Click any photo to enter large view mode:
- **Info Panel**: Click `i` icon to view detailed EXIF info (Camera, Aperture, ISO, GPS, etc.).
- **Live Photo**: If it's a Live Photo, hover or long-press to play the video part.
- **Download Original**: Supports downloading the original file.

### Video Playback
The system supports direct web playback of most common video formats. If incompatible, it is recommended to install decoding plugins in the browser or transcode before upload.

### Delete Photos
- **Move to Trash**: Click the delete icon to move photos to trash; they are not physically deleted immediately.
- **Empty Trash**: Run **Empty Trash** task in System Maintenance page to permanently delete files.

## 5. FAQ

**Q: Why can't I search for photos?**
A: Please ensure you have run the "Generate Semantic Vectors" task. Newly imported photos need AI processing before they can be searched.

**Q: No photos on the map?**
A: Only photos with GPS information appear on the map. Please run the "Update Location Info" task to parse coordinates into place names.

**Q: Can faces in videos be recognized?**
A: Yes. The system automatically extracts video frames for face detection. Please ensure you run the latest version of the "Face Recognition" task.
