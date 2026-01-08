# Plover Photos - AI 增强功能规划

本文档是 `Docs\规划设计.md` 的补充文档，专注于 Plover Photos 系统的 **AI 智能化扩展** 功能。基础架构、核心功能与数据模型请参考主设计文档。

## 1. AI 增强目标
通过引入本地运行的 AI 模型，实现照片的“语义化理解”与“智能化组织”，核心解决“找照片难”和“整理照片累”的问题。目标是让照片检索像对话一样自然。

## 2. 核心 AI 功能

### 2.1 语义搜索 (Semantic Search)
- **功能描述**: 支持自然语言描述搜索，不再局限于关键词匹配。
- **示例**:
  - "风和日丽的下午"
  - "秋天的大草原"
  - "雪中的红色汽车"
  - "海边的日落"
- **技术原理**: 利用多模态模型 (CLIP) 将图片和文本映射到同一向量空间，计算向量间的余弦相似度。

### 2.2 智能场景分类 (Scene Classification)
- **功能描述**: 自动识别照片拍摄场景并打上标签。
- **标签示例**: 海滩、山脉、城市、森林、室内、美食、宠物。
- **实现方式**: 基于 CLIP 的 Zero-shot (零样本) 分类能力，预定义场景词库进行匹配，无需额外训练分类模型。

### 2.3 人脸识别与聚类 (Face Recognition)
- **功能描述**: 自动检测照片中的人脸，识别同一人物，生成“人物相册”。
- **交互流程**:
  1. 系统后台自动扫描照片，检测并提取人脸特征。
  2. 自动聚类相似人脸。
  3. 用户在 UI 上为某个人物命名（如“张三”）。
  4. 系统自动将该聚类下的所有照片关联到“张三”。

### 2.4 OCR 文字识别
- **功能描述**: 提取照片中的文字信息（路牌、文档、截图）。
- **应用**: 支持通过图片包含的文字内容进行搜索。

## 3. 技术栈与模型选择

- **Embedding Model (语义向量)**: `sentence-transformers/clip-ViT-B-32-multilingual-v1`
  - **原因**: 支持 **中文** 的多语言 CLIP 模型，性能与速度平衡较好，适合个人服务器部署。
- **Face Recognition (人脸识别)**: `face_recognition` (基于 dlib) 或 `insightface`
  - **原因**: 本地运行成熟库，准确率高，无需联网。
- **OCR (文字识别)**: `PaddleOCR`
  - **原因**: 中文识别效果极佳，轻量级模型。
- **Vector Database (向量数据库)**: PostgreSQL + **pgvector**
  - **原因**: 复用主数据库，无需维护额外的向量数据库 (如 Milvus/Qdrant)，运维成本低，与 Django 集成紧密。
- **Task Queue**: Django Native Tasks Framework
  - **原因**: 复用主设计文档中确定的 Django 6.0 原生任务框架，统一异步任务处理机制。AI 推理任务（如 CLIP Embedding 生成、人脸检测）将作为标准的后台任务执行。

## 4. 数据模型扩展

这些模型是建立在主设计文档基础之上的扩展：

### Photo (扩展字段)
- **`embedding`**: `VectorField` (来自 `pgvector.django`)
  - 存储 CLIP 图像向量 (通常为 512 或 768 维)。
  - **索引**: 添加 HNSW (Hierarchical Navigable Small World) 索引以加速近似最近邻搜索。

### Face (新增实体)
- `photo`: ForeignKey to Photo (关联的照片)
- `encoding`: BinaryField 或 VectorField (存储 128 维人脸特征向量)
- `bounding_box`: JSONField (存储人脸坐标 `x, y, w, h`)
- `person`: ForeignKey to Person (关联的人物，可为空)

### Person (新增实体)
- `name`: CharField (人物姓名)
- `cover_face`: ForeignKey to Face (封面大头照)

## 5. AI 开发路线图

### 第一阶段：基础设施 (AI Foundation)
- [ ] 启用 PostgreSQL `pgvector` 插件。
- [ ] 在 Django 项目中安装并配置 `pgvector` 和 `sentence-transformers`。
- [ ] 编写 Django Command 脚本，验证模型加载与简单的推理测试。

### 第二阶段：语义搜索 (Semantic Search)
- [ ] **后台任务**: 实现 `generate_embedding_task`，批量为现有照片生成 CLIP Embeddings。
- [ ] **信号处理**: 监听照片上传事件，新照片自动触发 Embedding 生成任务。
- [ ] **API 接口**: 开发搜索 API (`/api/photos/search/`)，接收文本查询，返回相似照片列表。

### 第三阶段：智能整理 (Smart Organization)
- [ ] **场景分类**: 实现基于 CLIP Zero-shot 的场景分类任务，自动为照片添加 Tag。
- [ ] **OCR 集成**: 集成 PaddleOCR，提取文字并存入 Django 的 `SearchVector` 或单独字段。

### 第四阶段：人脸识别 (Face Cluster) (已完成)
- [x] **人脸检测**: 集成识脸库，实现人脸检测与特征提取任务。
- [x] **人脸聚类**: 实现人脸聚类算法 (如 DBSCAN 或 简单的阈值匹配)，将相似人脸归组。
- [x] **人物管理 API**: 开发人物管理 API (`/api/people/`)，支持前端进行重命名、合并与修正操作。
