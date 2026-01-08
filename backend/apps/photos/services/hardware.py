import os

def check_gpu_availability(silent=False):
    """检测 GPU 可用性"""
    gpu_info = {"available": False, "type": None, "details": "", "onnx_cuda": False}
    
    # 1. 尝试通过 onnxruntime 检测 (最贴近实际使用)
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        if 'CUDAExecutionProvider' in providers:
            try:
                # 构造一个极小的 ONNX 模型来真正测试 CUDA Provider 初始化
                import onnx
                from onnx import helper, TensorProto
                
                X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [1])
                Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [1])
                node_def = helper.make_node('Identity', ['X'], ['Y'])
                graph_def = helper.make_graph([node_def], 'test', [X], [Y])
                opset = helper.make_opsetid("", 11)
                model_def = helper.make_model(graph_def, producer_name='test', ir_version=8, opset_imports=[opset])
                model_bytes = model_def.SerializeToString()
                
                opts = ort.SessionOptions()
                opts.log_severity_level = 3
                sess = ort.InferenceSession(model_bytes, sess_options=opts, providers=['CUDAExecutionProvider'])
                
                gpu_info["available"] = True
                gpu_info["type"] = "NVIDIA (CUDA)"
                gpu_info["details"] = "ONNX Runtime CUDA Provider available"
                gpu_info["onnx_cuda"] = True
                return gpu_info
            except Exception:
                pass
    except:
        pass

    # 2. 尝试通过 PyTorch 检测 (备选方案)
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["type"] = "NVIDIA (CUDA)"
            gpu_info["details"] = f"{torch.cuda.get_device_name(0)} (Torch {torch.__version__})"
            return gpu_info
    except:
        pass

    # 3. 尝试检测 NVIDIA GPU (通过 nvidia-smi)
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            gpu_info["available"] = True
            gpu_info["type"] = "NVIDIA"
            gpu_info["details"] = result.stdout.strip()
            return gpu_info
    except:
        pass

    # 4. 尝试通过 OpenCV 检测 OpenCL (AMD/Intel/NVIDIA 通用)
    try:
        import cv2
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            gpu_info["available"] = True
            gpu_info["type"] = "OpenCL"
            gpu_info["details"] = "Generic OpenCL acceleration enabled"
            return gpu_info
    except:
        pass
        
    return gpu_info
