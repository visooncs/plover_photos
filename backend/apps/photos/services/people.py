from django.db.models import Avg
from apps.photos.models import Person, Face, Photo
import numpy as np
import json
from pgvector.django import CosineDistance

class PersonService:
    @staticmethod
    def get_merge_suggestions(threshold=0.2):
        """
        获取合并建议：寻找特征向量相近的人物
        优化版：使用 pgvector 的自连接在数据库层面完成 O(N^2) 比较，极大提升性能
        """
        from django.db import connection
        from apps.photos.models import Person
        
        # 1. 获取所有非隐藏人物的 ID 列表，用于过滤
        visible_person_ids = list(Person.objects.filter(is_hidden=False).values_list('id', flat=True))
        if not visible_person_ids:
            return []

        # 2. 获取所有忽略的合并对
        PersonIgnoredMerges = Person.ignored_merges.through
        ignored_pairs = set()
        all_ignored = PersonIgnoredMerges.objects.all().values_list('from_person_id', 'to_person_id')
        for p1_id, p2_id in all_ignored:
            ignored_pairs.add(tuple(sorted([str(p1_id), str(p2_id)])))

        # 3. 使用原生 SQL 在数据库内部进行向量相似度计算
        # 使用 CTE 计算平均向量，然后进行自连接筛选
        with connection.cursor() as cursor:
            sql = """
                WITH person_embeddings AS (
                    SELECT person_id, avg(embedding) as avg_vec
                    FROM photos_face 
                    WHERE person_id IS NOT NULL AND embedding IS NOT NULL
                    GROUP BY person_id
                )
                SELECT 
                    p1.person_id as id1, 
                    p2.person_id as id2, 
                    p1.avg_vec <=> p2.avg_vec as distance
                FROM person_embeddings p1
                JOIN person_embeddings p2 ON p1.person_id < p2.person_id
                WHERE p1.avg_vec <=> p2.avg_vec < %s
            """
            cursor.execute(sql, [threshold])
            rows = cursor.fetchall()

        if not rows:
            return []

        # 4. 过滤并构建结果
        # 先收集所有涉及的人物 ID 以便批量查询
        relevant_person_ids = set()
        candidate_suggestions = []
        
        visible_person_ids_set = set(str(pid) for pid in visible_person_ids)

        for id1, id2, dist in rows:
            sid1, sid2 = str(id1), str(id2)
            
            # 过滤隐藏人物
            if sid1 not in visible_person_ids_set or sid2 not in visible_person_ids_set:
                continue
                
            # 过滤已忽略的对
            if tuple(sorted([sid1, sid2])) in ignored_pairs:
                continue
            
            relevant_person_ids.add(id1)
            relevant_person_ids.add(id2)
            candidate_suggestions.append((id1, id2, dist))

        # 5. 批量获取人物对象（包含头像）
        people_map = {p.id: p for p in Person.objects.filter(id__in=relevant_person_ids).select_related('avatar')}
        
        suggestions = []
        for id1, id2, dist in candidate_suggestions:
            p1 = people_map.get(id1)
            p2 = people_map.get(id2)
            if p1 and p2:
                suggestions.append({
                    'person1': p1,
                    'person2': p2,
                    'distance': dist,
                    'confidence': round((1 - dist) * 100, 1)
                })
        
        return sorted(suggestions, key=lambda x: x['distance'])

    @staticmethod
    def get_similar_to_person(target_person, threshold=0.3):
        """
        寻找与指定人物相似的其他人物
        """
        target_vec = PersonService.get_person_representative_embedding(target_person)
        if target_vec is None:
            return []
            
        # 获取所有其他人物的平均向量
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT person_id, avg(embedding) 
                FROM photos_face 
                WHERE person_id IS NOT NULL AND person_id != %s AND embedding IS NOT NULL
                GROUP BY person_id
            """, [target_person.id])
            rows = cursor.fetchall()
            
        def parse_vector(v):
            if isinstance(v, str):
                return np.array(json.loads(v))
            return np.array(v)

        similar_people = []
        ignored_ids = set(target_person.ignored_merges.values_list('id', flat=True))
        
        # 获取人物信息以便显示
        other_people_map = {p.id: p for p in Person.objects.filter(is_hidden=False)}
        
        for row in rows:
            person_id = row[0]
            if person_id in ignored_ids or person_id not in other_people_map:
                continue
                
            other_vec = parse_vector(row[1])
            dist = PersonService.cosine_distance(target_vec, other_vec)
            
            if dist < threshold:
                similar_people.append({
                    'person': other_people_map[person_id],
                    'distance': dist,
                    'confidence': round((1 - dist) * 100, 1)
                })
                
        return sorted(similar_people, key=lambda x: x['distance'])

    @staticmethod
    def get_person_representative_embedding(person):
        """获取人物的代表性特征向量（目前取平均值）"""
        faces = person.faces.exclude(embedding__isnull=True)
        if not faces.exists():
            return None
        
        embeddings = [np.array(f.embedding) for f in faces]
        return np.mean(embeddings, axis=0)

    @staticmethod
    def cosine_distance(v1, v2):
        """计算余弦距离 (输入需为 numpy 数组)"""
        return 1 - np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    @staticmethod
    def auto_cluster_unlabeled_faces(threshold=0.15, min_samples=3):
        """
        使用快速聚类算法处理大量未标记人脸
        1. 尝试匹配已有人物
        2. 对剩余人脸进行 DBSCAN 聚类
        """
        from sklearn.cluster import DBSCAN
        import numpy as np
        from django.db import transaction
        from django.db import connections

        # 获取所有未标记且有向量的人脸
        # 针对 8 万张脸的大规模数据，我们分批处理向量加载
        self_qs = Face.objects.filter(person__isnull=True, embedding__isnull=False).only('id', 'embedding', 'photo_id')
        total_unlabeled = self_qs.count()
        
        if total_unlabeled == 0:
            return 0

        print(f"加载 {total_unlabeled} 个特征向量进行聚类分析...")
        unlabeled_faces = list(self_qs)
        labeled_count = 0
        
        # --- 第一阶段：尝试匹配已有人物 ---
        people = Person.objects.all()
        # 预先计算所有人物的代表向量
        people_vecs = []
        for p in people:
            v = PersonService.get_person_representative_embedding(p)
            if v is not None:
                people_vecs.append((p, v))
        
        remaining_faces = []
        if people_vecs:
            print(f"正在尝试匹配 {len(people_vecs)} 个已有人物...")
            for face in unlabeled_faces:
                best_match = None
                min_dist = threshold
                
                face_vec = np.array(face.embedding)
                for person, p_vec in people_vecs:
                    # 使用矩阵运算加速对比
                    dist = PersonService.cosine_distance(face_vec, p_vec)
                    if dist < min_dist:
                        min_dist = dist
                        best_match = person
                
                if best_match:
                    face.person = best_match
                    face.save()
                    best_match.photos.add(face.photo_id)
                    # 确保人物有头像
                    if not best_match.avatar:
                        best_match.avatar = face.photo
                        best_match.save(update_fields=['avatar'])
                    labeled_count += 1
                else:
                    remaining_faces.append(face)
        else:
            remaining_faces = unlabeled_faces

        if not remaining_faces:
            return labeled_count

        # --- 第二阶段：对剩余人脸进行快速聚类 (DBSCAN) ---
        print(f"对剩余 {len(remaining_faces)} 张人脸进行 DBSCAN 聚类发现新人物...")
        
        # 准备数据矩阵
        embeddings = np.array([f.embedding for f in remaining_faces])
        
        # 确保向量归一化，以便余弦距离计算更准确
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # 避免除以 0
        norms[norms == 0] = 1
        embeddings = embeddings / norms
        
        # 余弦距离下的 DBSCAN
        # eps 是距离阈值，余弦距离 = 1 - 相似度
        clustering = DBSCAN(eps=threshold, min_samples=min_samples, metric='cosine', n_jobs=-1).fit(embeddings)
        
        labels = clustering.labels_
        unique_labels = set(labels)
        
        print(f"聚类完成，发现 {len(unique_labels) - (1 if -1 in unique_labels else 0)} 个潜在新人物群组")
        
        # 处理每个簇
        current_person_count = Person.objects.count()
        for label in unique_labels:
            if label == -1: # 噪声点
                continue
            
            # 获取该簇的所有索引
            indices = np.where(labels == label)[0]
            cluster_faces = [remaining_faces[i] for i in indices]
            
            # 为该簇创建一个新人物
            with transaction.atomic():
                new_person = Person.objects.create(
                    name=f"人物_{current_person_count + 1}"
                )
                current_person_count += 1
                
                # 批量更新关联
                face_ids = [f.id for f in cluster_faces]
                Face.objects.filter(id__in=face_ids).update(person=new_person)
                
                # 批量添加照片关联 (ManyToMany)
                photo_ids = list(set(f.photo_id for f in cluster_faces))
                new_person.photos.add(*photo_ids)
                
                # 设置第一个脸的照片为头像，确保在列表页能看到头像
                if cluster_faces:
                    new_person.avatar_id = cluster_faces[0].photo_id
                    new_person.save()
                
                labeled_count += len(cluster_faces)
        
        # 任务结束后清理连接
        connections.close_all()
        return labeled_count
