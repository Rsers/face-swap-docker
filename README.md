# 面部替换API服务 (Docker部署版)

这是一个基于InsightFace开发的面部替换API服务，可通过Docker容器快速部署。

## 功能特点

- 基于FastAPI和InsightFace实现
- 支持将源图片中的人脸替换到目标图片中
- 支持选择源图片中特定索引的人脸
- 自动识别并替换目标图片中最大的人脸
- 通过API形式提供服务，方便前端页面调用
- 自动下载并缓存所需模型

## 快速开始

### 前提条件

- 安装Docker和Docker Compose
- 确保服务器具有足够的CPU资源和内存

### 部署步骤

1. 将整个文件夹复制到服务器上

2. 进入项目目录
   ```bash
   cd face-swap-docker
   ```

3. 构建并启动容器
   ```bash
   docker-compose up -d
   ```

4. 服务启动后，API将在以下地址可用：
   ```
   http://你的服务器IP:8000
   ```

### API接口说明

#### 1. 面部替换接口

- URL: `/face_swap`
- 方法: `POST`
- 参数:
  - `source_image`: (文件) 源图片，包含要提取的面部
  - `target_image`: (文件) 目标图片，将被替换面部
  - `output_name`: (可选) 输出文件名
  - `face_index`: (默认0) 使用源图像中的第几个人脸

- 返回:
  - `result_url`: 结果图片URL
  - `message`: 处理结果信息

#### 2. 获取图像接口

- URL: `/image/{image_path}`
- 方法: `GET`
- 参数:
  - `image_path`: 图像路径

#### 3. 首页信息接口

- URL: `/`
- 方法: `GET`
- 返回: API服务信息和可用端点

## 示例调用

### 使用curl调用

```bash
curl -X POST "http://localhost:8000/face_swap" \
  -F "source_image=@/path/to/source.jpg" \
  -F "target_image=@/path/to/target.jpg" \
  -F "face_index=0"
```

### 使用Python调用

```python
import requests

url = "http://localhost:8000/face_swap"

files = {
    'source_image': open('source.jpg', 'rb'),
    'target_image': open('target.jpg', 'rb')
}

data = {
    'face_index': 0
}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result['result_url'])
```

### 使用JavaScript调用

```javascript
const formData = new FormData();
formData.append('source_image', sourceImageFile);
formData.append('target_image', targetImageFile);
formData.append('face_index', 0);

fetch('http://localhost:8000/face_swap', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('结果图片:', data.result_url);
});
```

## 注意事项

1. 首次启动时，会自动下载模型文件，可能需要几分钟时间
2. 建议使用具有较高CPU性能的服务器以获得更好的处理速度
3. 默认使用CPU进行推理，如需使用GPU，请修改`main.py`中的provider配置

## 性能优化

- 为提高处理速度，模型文件存储在Docker卷中，即使容器重启也不需要重新下载
- 如果您的服务器有GPU，可以考虑使用GPU版本来加速处理