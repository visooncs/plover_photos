from sentence_transformers import SentenceTransformer
import os

model_name = 'clip-ViT-B-32'
save_path = os.path.join('models', 'huggingface', 'clip-ViT-B-32')

print(f"正在下载模型 {model_name} 到 {save_path}...")

try:
    # 强制下载到指定目录
    model = SentenceTransformer(model_name, cache_folder=os.path.join('models', 'huggingface'))
    model.save(save_path)
    print(f"模型下载并保存成功！路径: {save_path}")
    
    # 检查关键文件
    if os.path.exists(os.path.join(save_path, 'config.json')):
        print("验证成功: config.json 已存在。")
    else:
        print("警告: 未找到 config.json，可能保存格式不完整。")
        
except Exception as e:
    print(f"下载失败: {str(e)}")
