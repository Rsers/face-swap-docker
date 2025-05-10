FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    python3-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1-mesa-glx \
    wget \
    git \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY main.py requirements.txt ./
COPY static/ ./static/
COPY docs/ ./docs/
COPY gfpgan/ ./gfpgan/

# 创建必要的目录
RUN mkdir -p ~/.insightface/models/
RUN mkdir -p ~/.gfpgan/weights/
RUN mkdir -p temp

# 下载模型文件 - 从GitHub Releases获取
RUN echo "Downloading model files from GitHub Releases..." && \
    # 下载并安装inswapper_128.onnx
    wget -q https://github.com/Rsers/face-swap-docker/releases/download/v1.0.0/inswapper_128.onnx -O ~/.insightface/models/inswapper_128.onnx && \
    # 下载并安装buffalo_l.zip
    wget -q https://github.com/Rsers/face-swap-docker/releases/download/v1.0.0/buffalo_l.zip -O /tmp/buffalo_l.zip && \
    unzip -q /tmp/buffalo_l.zip -d ~/.insightface/models/ && \
    rm /tmp/buffalo_l.zip && \
    # 下载并安装GFPGAN模型文件
    wget -q https://github.com/Rsers/face-swap-docker/releases/download/v1.0.0/GFPGANv1.4.pth -O ~/.gfpgan/weights/GFPGANv1.4.pth && \
    wget -q https://github.com/Rsers/face-swap-docker/releases/download/v1.0.0/detection_Resnet50_Final.pth -O ~/.gfpgan/weights/detection_Resnet50_Final.pth && \
    wget -q https://github.com/Rsers/face-swap-docker/releases/download/v1.0.0/parsing_parsenet.pth -O ~/.gfpgan/weights/parsing_parsenet.pth && \
    echo "All model files downloaded successfully."

# 安装Python依赖
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]