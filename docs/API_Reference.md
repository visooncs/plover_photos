# Plover Photos API Reference

This document describes the main endpoints and usage of the backend API.

## Basics
- **Base URL**: `/api`
- **Authentication**: Currently supports Session authentication (Admin panel login) or no authentication (Development mode).
- **Response Format**: JSON

## 1. Core Resources

### 1.1 Photos

#### Get Photo List
`GET /api/photos/`

Supports pagination and various filtering parameters.

**Parameters**:
- `page`: Page number (default 1)
- `page_size`: Items per page (default 50)
- `captured_at__year`: Filter by year (e.g., `2024`)
- `location_name`: Filter by location name
- `people`: Person ID (filter photos containing specific person)
- `search`: Semantic search keyword (requires vector index generation)

**Response Example**:
```json
{
  "count": 1024,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "id": "uuid...",
      "file_path": "/mnt/d/photos/img_001.jpg",
      "captured_at": "2024-01-01T12:00:00Z",
      "width": 4032,
      "height": 3024,
      "is_live_photo": true,
      "thumbnail": "/api/photos/{id}/serve/?size=300&crop=1",
      "faces": [...]
    }
  ]
}
```

#### Get Single Photo Details
`GET /api/photos/{id}/`

#### Serve Photo File
`GET /api/photos/{id}/serve/`

**Parameters**:
- `size`: Thumbnail size (e.g., `300`, `800`). Returns original if omitted.
- `crop`: Whether to crop to square (`1` or `0`).

### 1.2 Albums

#### Get Album List
`GET /api/albums/`

#### Get Album Details
`GET /api/albums/{id}/`

### 1.3 People

#### Get People List
`GET /api/people/`

Returns clustered people list, usually containing cover image and photo count.

#### Update Person Info
`PATCH /api/people/{id}/`

Used to modify person name.
```json
{
  "name": "New Name"
}
```

## 2. Maintenance

Used to manage and trigger background asynchronous tasks.

### Get Task List
`GET /api/maintenance/`

Returns recently executed tasks and their status.

**Response Example**:
```json
[
  {
    "id": "uuid...",
    "name": "scan_photos",
    "status": "completed", // pending, running, completed, failed
    "progress": 100,
    "created_at": "...",
    "logs": "Scanning /mnt/d/...\nFound 5 new files."
  }
]
```

### Trigger New Task
`POST /api/maintenance/{id}/run/`

Note: This is usually for retrying existing task records, or creating new tasks via specific endpoints.
(Frontend currently creates tasks via predefined command lists)

**Supported Task Types (Command Names)**:
- `scan_photos`: Scan photo library
- `process_faces`: Face recognition
- `cluster_people`: Face clustering
- `process_embeddings`: Generate semantic vectors
- `generate_memories`: Generate memories
- `update_gps`: Update location info
- `cleanup_trash`: Empty trash

## 3. Others

### Geo (Locations)
`GET /api/geo/locations/`
Get list of all identified locations.

### Memories
`GET /api/memories/`
Get generated smart memory cards.
