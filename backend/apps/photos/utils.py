import os

def resolve_docker_path(path):
    """
    在 Docker 环境下，将宿主机路径映射为容器内路径
    通过环境变量 DOCKER_PATH_MAPPINGS 配置映射关系
    格式: "HostPath=>ContainerPath;HostPath2=>ContainerPath2"
    示例: "D:\\=>/mnt/d;E:\\=>/mnt/e"
    """
    mappings = os.environ.get('DOCKER_PATH_MAPPINGS', '')
    # 自动去除可能被错误包含的引号
    if mappings:
        mappings = mappings.strip("'").strip('"')
        
    if not mappings:
        return path

    # 统一路径分隔符以便处理
    path_str = str(path)
    
    for mapping in mappings.split(';'):
        if '=>' not in mapping:
            continue
            
        host_prefix, container_prefix = mapping.split('=>', 1)
        host_prefix = host_prefix.strip()
        container_prefix = container_prefix.strip()
        
        # 简单的大小写不敏感匹配 (针对 Windows 宿主机)
        if path_str.lower().startswith(host_prefix.lower()):
            # 提取相对路径部分
            rel_path = path_str[len(host_prefix):]
            # 将 Windows 反斜杠转换为正斜杠
            rel_path = rel_path.replace('\\', '/').lstrip('/')
            # 拼接容器路径
            new_path = os.path.join(container_prefix, rel_path)
            return new_path

    return path
