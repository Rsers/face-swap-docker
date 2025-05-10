# API 使用示例

本文档提供了面部增强和替换API的完整使用示例。

## 1. 人脸增强 API

### 1.1 基础调用
使用curl发送POST请求进行人脸增强：

```bash
curl -X POST "http://localhost:8001/enhance_face" \
  -F "image=@/path/to/your/image.jpg" \
  -F "output_name=enhanced_result"
```

### 1.2 Python示例
使用Python requests库调用API：

```python
import requests

def enhance_face(image_path, output_name):
    url = "http://localhost:8001/enhance_face"
    
    # 准备文件和参数
    files = {
        'image': open(image_path, 'rb')
    }
    data = {
        'output_name': output_name
    }
    
    # 发送请求
    response = requests.post(url, files=files, data=data)
    
    # 检查响应
    if response.status_code == 200:
        result = response.json()
        print(f"增强成功！结果URL: {result['result_url']}")
        print(f"消息: {result['message']}")
    else:
        print(f"错误: {response.text}")

# 使用示例
enhance_face("image.jpg", "enhanced_output")
```

## 2. 人脸替换 API

### 2.1 基础调用
使用curl发送POST请求进行人脸替换：

```bash
curl -X POST "http://localhost:8001/face_swap" \
  -F "source_image=@/path/to/source.jpg" \
  -F "target_image=@/path/to/target.jpg" \
  -F "output_name=swapped_result" \
  -F "face_index=0"
```

### 2.2 Python示例
使用Python requests库调用API：

```python
import requests

def swap_face(source_path, target_path, output_name, face_index=0):
    url = "http://localhost:8001/face_swap"
    
    # 准备文件和参数
    files = {
        'source_image': open(source_path, 'rb'),
        'target_image': open(target_path, 'rb')
    }
    data = {
        'output_name': output_name,
        'face_index': face_index
    }
    
    # 发送请求
    response = requests.post(url, files=files, data=data)
    
    # 检查响应
    if response.status_code == 200:
        result = response.json()
        print(f"替换成功！结果URL: {result['result_url']}")
        print(f"消息: {result['message']}")
    else:
        print(f"错误: {response.text}")

# 使用示例
swap_face("source.jpg", "target.jpg", "swapped_output", face_index=0)
```

## 3. 实际测试案例

### 3.1 人脸增强测试
使用示例图片测试人脸增强API：

```bash
# 使用Blake_Lively.jpg测试
curl -X POST "http://localhost:8001/enhance_face" \
  -F "image=@/home/ubuntu/GFPGAN-1.3.8/inputs/whole_imgs/Blake_Lively.jpg" \
  -F "output_name=enhanced_blake"

# 使用高分辨率图片测试
curl -X POST "http://localhost:8001/enhance_face" \
  -F "image=@/home/ubuntu/GFPGAN-1.3.8/inputs/whole_imgs/00.jpg" \
  -F "output_name=enhanced_test2"
```

### 3.2 人脸替换测试
使用示例图片测试人脸替换API：

```bash
# 替换单个人脸
curl -X POST "http://localhost:8001/face_swap" \
  -F "source_image=@/home/ubuntu/GFPGAN-1.3.8/inputs/whole_imgs/Blake_Lively.jpg" \
  -F "target_image=@/home/ubuntu/GFPGAN-1.3.8/inputs/whole_imgs/00.jpg" \
  -F "output_name=swapped_example"

# 指定源图片中的特定人脸
curl -X POST "http://localhost:8001/face_swap" \
  -F "source_image=@source_multi_faces.jpg" \
  -F "target_image=@target.jpg" \
  -F "output_name=swapped_specific" \
  -F "face_index=1"
```

## 4. 响应格式

### 4.1 成功响应
成功时API返回JSON格式：
```json
{
    "result_url": "http://localhost:8001/image/results/output.jpg",
    "message": "处理成功信息"
}
```

### 4.2 错误响应
失败时API返回错误信息：
```json
{
    "detail": "错误描述信息"
}
```

## 5. 注意事项

1. 所有图片处理都是异步的，API会立即返回响应
2. 处理后的图片可以通过返回的URL访问
3. 临时文件会自动清理
4. 支持的图片格式：jpg, jpeg, png
5. 建议图片分辨率不要太大，推荐在2048x2048以内
6. face_index参数在源图片包含多个人脸时很有用