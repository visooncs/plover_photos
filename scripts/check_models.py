import os
import sys
import numpy as np
from PIL import Image

# 将 backend 目录加入路径，以便复用硬件检测逻辑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

def check_insightface():
    print("=== 1. 检查 InsightFace (人脸识别) 模型 ===")
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "insightface"))
    model_dir = os.path.join(local_path, "models", "buffalo_l")
    
    if not os.path.exists(model_dir):
        print(f"[失败] 未找到模型目录: {model_dir}")
        return False
    
    print(f"[OK] 找到模型目录: {model_dir}")
    print(f"目录文件: {os.listdir(model_dir)}")
    
    try:
        import insightface
        from insightface.app import FaceAnalysis
        
        # 强制指定根目录
        app = FaceAnalysis(name='buffalo_l', root=local_path, providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))
        
        # 测试推理
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        app.get(test_img)
        print("[成功] InsightFace 模型初始化并推理成功！")
        return True
    except Exception as e:
        print(f"[失败] InsightFace 加载/测试失败: {e}")
        return False

def check_clip():
    print("\n=== 2. 检查 CLIP (语义搜索) 模型 ===")
    huggingface_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "huggingface"))
    
    model_name = 'clip-ViT-B-32'
    possible_dirs = [
        os.path.join(huggingface_base, f"sentence-transformers_{model_name}"),
        os.path.join(huggingface_base, model_name)
    ]
    
    target_dir = None
    for d in possible_dirs:
        if os.path.exists(os.path.join(d, "config.json")):
            target_dir = d
            break
            
    if not target_dir:
        print(f"[失败] 在以下位置未找到完整的 CLIP 模型 (需包含 config.json):")
        for d in possible_dirs: print(f"  - {d}")
        return False
    
    print(f"[OK] 找到 CLIP 模型目录: {target_dir}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 设置离线模式环境变量
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        
        print(f"正在从本地加载模型...")
        model = SentenceTransformer(target_dir, device='cpu')
        
        # 测试推理
        test_emb = model.encode(["这是一张测试照片"])
        print(f"[成功] CLIP 模型加载成功！向量维度: {test_emb.shape}")
        return True
    except Exception as e:
        print(f"[失败] CLIP 加载/测试失败: {e}")
        return False

if __name__ == "__main__":
    print("模型可用性检查工具\n")
    is_ok = check_insightface()
    clip_ok = check_clip()
    
    print("\n" + "="*30)
    if is_ok and clip_ok:
        print("✅ 所有模型均已就绪，可以启动 Docker 服务！")
    else:
        print("❌ 部分模型存在问题，请根据上方错误信息处理。")
    print("="*30)
