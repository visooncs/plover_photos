import os
import sys
import socket

# 设置镜像源
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

def test_connection(host, port=443):
    try:
        socket.setdefaulttimeout(5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def download_clip():
    repo_id = "sentence-transformers/clip-ViT-B-32"
    # 这里的路径必须与 docker-compose 挂载的宿主机路径一致
    local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "huggingface", "sentence-transformers_clip-ViT-B-32"))
    
    print(f"=== 正在检查网络连接 ===")
    if test_connection("hf-mirror.com"):
        print("[OK] 能够连接到 hf-mirror.com")
    else:
        print("[ERROR] 无法连接到 hf-mirror.com，请检查您的代理设置或网络。")
        print("建议：请手动访问 https://hf-mirror.com/sentence-transformers/clip-ViT-B-32 下载文件。")
        return

    print(f"\n=== 正在从镜像源下载 {repo_id} ===")
    print(f"目标目录: {local_dir}")
    
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            # 增加重试次数
            max_workers=4
        )
        print("\n[成功] CLIP 模型下载完成！")
    except Exception as e:
        print(f"\n[失败] 下载出错: {e}")
        print("\n--- 手动下载指南 ---")
        print(f"1. 访问 https://hf-mirror.com/{repo_id}/tree/main")
        print(f"2. 下载所有文件并存放到目录: {local_dir}")

if __name__ == "__main__":
    download_clip()
