from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
import shutil
import uuid
import sys
from typing import Optional, List
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
import time
import requests
from gfpgan import GFPGANer
import torch

app = FastAPI(
    title="面部替换与增强 API",
    description="基于 insightface 和 GFPGAN 的面部替换与增强服务",
    version="1.0.0",
)

# 配置CORS，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 全局变量，用于存储面部分析器和面部交换模型
face_analyzer = None
face_swapper = None
gfpgan_enhancer = None  # GFPGAN模型

# 初始化函数
def init_models():
    """初始化面部分析和交换模型"""
    global face_analyzer, face_swapper
    
    # 检查模型是否已经加载
    if face_analyzer is not None and face_swapper is not None:
        return
    
    try:
        # 设置日志级别
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("insightface")
        logger.setLevel(logging.ERROR)
        
        # 初始化面部分析器
        face_analyzer = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        face_analyzer.prepare(ctx_id=0, det_size=(640, 640))
        
        # 初始化面部交换模型
        model_path = os.path.expanduser('~/.insightface/models/inswapper_128.onnx')
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # 如果模型不存在，尝试下载
        if not os.path.isfile(model_path):
            print("面部交换模型不存在，正在下载...")
            
            # 使用指定的链接下载模型
            try:
                # 使用提供的GitHub链接下载模型
                model_url = "https://github.com/dream80/roop_colab/releases/download/v0.0.1/inswapper_128.onnx"
                print(f"从 {model_url} 下载模型...")
                response = requests.get(model_url, stream=True)
                response.raise_for_status()  # 确保请求成功
                
                with open(model_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"模型已下载到 {model_path}")
            except Exception as download_err:
                print(f"模型下载失败: {str(download_err)}")
                raise
        
        # 加载面部交换模型
        face_swapper = insightface.model_zoo.get_model(model_path, providers=['CPUExecutionProvider'])
        print("面部交换模型已成功加载")
    except Exception as e:
        print(f"模型加载失败: {str(e)}")
        raise

def init_gfpgan():
    """初始化GFPGAN模型"""
    global gfpgan_enhancer
    
    if gfpgan_enhancer is not None:
        return
    
    try:
        # 设置模型路径
        model_path = os.path.expanduser('~/.gfpgan/weights/GFPGANv1.4.pth')
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # 如果模型不存在，从GFPGAN-1.3.8目录复制
        if not os.path.isfile(model_path):
            print("GFPGAN模型不存在，正在复制...")
            gfpgan_path = "/home/ubuntu/GFPGAN-1.3.8/experiments/pretrained_models/GFPGANv1.4.pth"
            shutil.copy2(gfpgan_path, model_path)
            print(f"模型已复制到 {model_path}")
        
        # 初始化GFPGAN
        gfpgan_enhancer = GFPGANer(
            model_path=model_path,
            upscale=2,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=None
        )
        print("GFPGAN模型已成功加载")
    except Exception as e:
        print(f"GFPGAN模型加载失败: {str(e)}")
        raise

def enhance_face(input_img, output_path):
    """使用GFPGAN进行面部增强和超分辨率处理"""
    try:
        # 确保模型已加载
        if gfpgan_enhancer is None:
            init_gfpgan()
        
        # 读取图像
        img = cv2.imread(input_img)
        if img is None:
            return False, "无法读取输入图像"
        
        # 使用GFPGAN处理图像
        _, _, enhanced_img = gfpgan_enhancer.enhance(
            img,
            has_aligned=False,
            only_center_face=False,
            paste_back=True
        )
        
        # 保存结果
        cv2.imwrite(output_path, enhanced_img)
        
        return True, "面部增强成功"
    except Exception as e:
        return False, f"面部增强失败: {str(e)}"

# 面部交换函数
def swap_face_insightface(source_img, target_img, output_path, face_index=0):
    """使用 insightface 进行面部交换"""
    try:
        # 确保模型已加载
        if face_analyzer is None or face_swapper is None:
            init_models()
        
        # 读取图像
        source = cv2.imread(source_img)
        target = cv2.imread(target_img)
        if source is None or target is None:
            return False, "无法读取源图像或目标图像"
        
        # 分析源图像的面部
        source_faces = face_analyzer.get(source)
        if not source_faces:
            return False, "在源图像中未检测到面部"
            
        # 分析目标图像的面部
        target_faces = face_analyzer.get(target)
        if not target_faces:
            return False, "在目标图像中未检测到面部"
        
        # 获取源面部 (使用指定的索引，如果可用)
        if face_index < 0 or face_index >= len(source_faces):
            source_face = source_faces[0]
            face_message = f"使用第一个面部 (共检测到 {len(source_faces)} 个)"
        else:
            source_face = source_faces[face_index]
            face_message = f"使用第 {face_index+1} 个面部 (共检测到 {len(source_faces)} 个)"
        
        # 找出目标图像中面积最大的人脸
        if len(target_faces) > 1:
            # 计算每个人脸边界框的面积
            face_areas = []
            for face in target_faces:
                bbox = face.bbox
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                face_areas.append(area)
            
            # 获取面积最大的人脸
            largest_face_idx = face_areas.index(max(face_areas))
            target_face = target_faces[largest_face_idx]
            face_message += f"，只替换目标图像中最大的人脸 (共检测到 {len(target_faces)} 个)"
        else:
            target_face = target_faces[0]
            face_message += f"，替换目标图像中唯一的人脸"
        
        # 只替换面积最大的目标人脸
        result = target.copy()
        result = face_swapper.get(result, target_face, source_face, paste_back=True)
        
        # 保存结果
        cv2.imwrite(output_path, result)
        
        return True, f"面部交换成功 ({face_message})"
    except Exception as e:
        return False, f"面部交换失败: {str(e)}"

@app.get("/")
async def read_root():
    """API 主页"""
    return {
        "message": "面部替换与增强 API 服务",
        "version": "1.0.0",
        "endpoints": {
            "/face_swap": "面部替换接口",
            "/enhance_face": "面部增强与修复接口",
            "/image/{image_name}": "获取图像",
            "/image_url": "获取示例图像URL",
            "/face_swap_and_enhance": "面部替换与增强接口"
        }
    }

@app.get("/image/{image_path:path}")
async def get_image(image_path: str):
    """
    获取指定路径的图片
    
    - **image_path**: 图片路径，可以包含子目录
    """
    image_full_path = Path(f"static/images/{image_path}")
    
    if not image_full_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    
    return FileResponse(image_full_path)

@app.get("/image_url")
async def get_image_url():
    """
    返回特定图片的URL示例
    """
    request_url = "http://localhost:8001"
    return JSONResponse({
        "source_url": f"{request_url}/image/source.jpg",
        "target_url": f"{request_url}/image/target.jpg",
        "result_example": f"{request_url}/image/results/result_example.jpg"
    })

# 后台任务函数：清理临时文件
def cleanup_temp_files(paths_to_remove: List[str]):
    for path in paths_to_remove:
        if os.path.exists(path):
            os.remove(path)

@app.post("/face_swap")
async def face_swap(
    background_tasks: BackgroundTasks,
    source_image: UploadFile = File(..., description="源图片，包含要提取的面部"),
    target_image: UploadFile = File(..., description="目标图片，将被替换面部"),
    output_name: Optional[str] = Form(None, description="输出文件名，如不提供则自动生成"),
    face_index: int = Form(0, description="要使用的面部索引（当源图像有多个面部时）")
):
    """
    执行面部替换：将源图片的面部替换到目标图片上
    
    - **source_image**: 源图片，包含要提取的面部
    - **target_image**: 目标图片，将被替换面部
    - **output_name**: 输出文件名，如不提供则自动生成
    - **face_index**: 要使用的面部索引（当源图像有多个面部时）
    
    返回:
    - **result_url**: 结果图片的URL
    - **message**: 处理结果消息
    """
    # 创建临时目录用于存储上传的图像
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    # 生成唯一文件名
    source_path = temp_dir / f"{uuid.uuid4()}{os.path.splitext(source_image.filename)[1]}"
    target_path = temp_dir / f"{uuid.uuid4()}{os.path.splitext(target_image.filename)[1]}"
    
    paths_to_cleanup = [str(source_path), str(target_path)]
    
    # 保存上传的图像
    try:
        with open(source_path, "wb") as buffer:
            shutil.copyfileobj(source_image.file, buffer)
        
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(target_image.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法保存上传的图像: {str(e)}")
    
    # 设置输出路径
    output_dir = Path("static/images/results")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if output_name:
        output_path = output_dir / f"{output_name}{os.path.splitext(target_image.filename)[1]}"
    else:
        output_path = output_dir / f"result_{uuid.uuid4()}{os.path.splitext(target_image.filename)[1]}"
    
    try:
        # 确保模型已加载
        init_models()
        
        # 执行面部替换
        success, message = swap_face_insightface(
            str(source_path), 
            str(target_path), 
            str(output_path),
            face_index=face_index
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"面部替换失败: {message}")
            
        # 获取请求的主机域名（使用实际运行的端口）
        request_host = "http://localhost:8001"
            
        # 返回结果图像的URL
        result_url = f"{request_host}/image/results/{output_path.name}"
        
        # 添加后台任务清理临时文件
        background_tasks.add_task(cleanup_temp_files, paths_to_cleanup)
        
        return JSONResponse({
            "result_url": result_url,
            "message": message
        })
    except Exception as e:
        # 添加后台任务清理临时文件
        background_tasks.add_task(cleanup_temp_files, paths_to_cleanup)
        raise HTTPException(status_code=500, detail=f"面部替换过程中发生错误: {str(e)}")

@app.post("/enhance_face")
async def face_enhance(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="需要增强的图片"),
    output_name: Optional[str] = Form(None, description="输出文件名，如不提供则自动生成")
):
    """
    执行面部增强：对图片中的人脸进行超分辨率和修复处理
    
    - **image**: 需要增强的图片
    - **output_name**: 输出文件名，如不提供则自动生成
    
    返回:
    - **result_url**: 结果图片的URL
    - **message**: 处理结果消息
    """
    # 创建临时目录用于存储上传的图像
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    # 生成唯一文件名
    input_path = temp_dir / f"{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"
    paths_to_cleanup = [str(input_path)]
    
    # 保存上传的图像
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法保存上传的图像: {str(e)}")
    
    # 设置输出路径
    output_dir = Path("static/images/results")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if output_name:
        output_path = output_dir / f"{output_name}{os.path.splitext(image.filename)[1]}"
    else:
        output_path = output_dir / f"enhanced_{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"
    
    try:
        # 执行面部增强
        success, message = enhance_face(str(input_path), str(output_path))
        
        if not success:
            raise HTTPException(status_code=500, detail=f"面部增强失败: {message}")
        
        # 获取请求的主机域名（使用实际运行的端口）
        request_host = "http://localhost:8001"
        
        # 返回结果图像的URL
        result_url = f"{request_host}/image/results/{output_path.name}"
        
        # 添加后台任务清理临时文件
        background_tasks.add_task(cleanup_temp_files, paths_to_cleanup)
        
        return JSONResponse({
            "result_url": result_url,
            "message": message
        })
    except Exception as e:
        # 添加后台任务清理临时文件
        background_tasks.add_task(cleanup_temp_files, paths_to_cleanup)
        raise HTTPException(status_code=500, detail=f"面部增强过程中发生错误: {str(e)}")

@app.post("/face_swap_and_enhance")
async def face_swap_and_enhance(
    background_tasks: BackgroundTasks,
    source_image: UploadFile = File(..., description="源图片，包含要提取的面部"),
    target_image: UploadFile = File(..., description="目标图片，将被替换面部"),
    output_name: Optional[str] = Form(None, description="输出文件名，如不提供则自动生成"),
    face_index: int = Form(0, description="要使用的面部索引（当源图像有多个面部时）")
):
    """
    执行面部替换并增强：将源图片的面部替换到目标图片上，然后进行面部增强处理
    
    - **source_image**: 源图片，包含要提取的面部
    - **target_image**: 目标图片，将被替换面部
    - **output_name**: 输出文件名，如不提供则自动生成
    - **face_index**: 要使用的面部索引（当源图像有多个面部时）
    
    返回:
    - **result_url**: 结果图片的URL
    - **message**: 处理结果消息
    """
    # 创建临时目录用于存储上传的图像和中间结果
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    # 生成唯一文件名
    source_path = temp_dir / f"{uuid.uuid4()}{os.path.splitext(source_image.filename)[1]}"
    target_path = temp_dir / f"{uuid.uuid4()}{os.path.splitext(target_image.filename)[1]}"
    swap_result_path = temp_dir / f"swap_{uuid.uuid4()}{os.path.splitext(target_image.filename)[1]}"
    
    paths_to_cleanup = [str(source_path), str(target_path), str(swap_result_path)]
    
    # 保存上传的图像
    try:
        with open(source_path, "wb") as buffer:
            shutil.copyfileobj(source_image.file, buffer)
        
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(target_image.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法保存上传的图像: {str(e)}")
    
    # 设置最终输出路径
    output_dir = Path("static/images/results")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if output_name:
        output_path = output_dir / f"{output_name}{os.path.splitext(target_image.filename)[1]}"
    else:
        output_path = output_dir / f"enhanced_swap_{uuid.uuid4()}{os.path.splitext(target_image.filename)[1]}"
    
    try:
        # 确保模型已加载
        init_models()
        init_gfpgan()
        
        # 步骤1: 执行面部替换
        success, swap_message = swap_face_insightface(
            str(source_path), 
            str(target_path), 
            str(swap_result_path),
            face_index=face_index
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"面部替换失败: {swap_message}")
        
        # 步骤2: 对替换后的结果进行面部增强
        success, enhance_message = enhance_face(str(swap_result_path), str(output_path))
        
        if not success:
            raise HTTPException(status_code=500, detail=f"面部增强失败: {enhance_message}")
        
        # 获取请求的主机域名（使用实际运行的端口）
        request_host = "http://localhost:8001"
        
        # 返回结果图像的URL
        result_url = f"{request_host}/image/results/{output_path.name}"
        
        # 添加后台任务清理临时文件
        background_tasks.add_task(cleanup_temp_files, paths_to_cleanup)
        
        return JSONResponse({
            "result_url": result_url,
            "message": f"面部替换和增强成功! {swap_message}，并且已进行面部增强处理"
        })
    except Exception as e:
        # 添加后台任务清理临时文件
        background_tasks.add_task(cleanup_temp_files, paths_to_cleanup)
        raise HTTPException(status_code=500, detail=f"处理过程中发生错误: {str(e)}")
