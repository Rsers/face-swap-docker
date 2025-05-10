# 面部替换与增强API服务 (Docker一键部署版)

这是一个基于InsightFace和GFPGAN开发的面部替换与增强API服务，可通过Docker容器快速部署。

## 部署方式选择

本项目提供两种部署方式，请根据您的需求和网络条件选择合适的方式：

### 方式一：下载预构建的Docker镜像文件（推荐，更快速）

通过从腾讯云COS桶下载已构建好的Docker镜像文件(.tar)，可以快速完成部署，无需等待构建过程。适合：
- 需要快速部署的场景
- 服务器带宽有限或网络不稳定的环境
- 不需要修改源代码的用户

可选择从以下区域的COS桶下载（根据您的地理位置选择较近的区域以获得更快下载速度）：
- 广州区域 (中国)
- 首尔区域 (韩国)

### 方式二：通过源代码构建Docker镜像（更灵活）

通过Docker Compose从源代码构建镜像并部署。适合：
- 需要自定义或修改源代码的场景
- 希望了解项目构建过程的用户
- 需要对项目进行二次开发的场景

下面将详细介绍这两种部署方式的具体步骤。

## 功能特点

- 基于FastAPI、InsightFace和GFPGAN实现
- 三大核心功能：
  - **面部替换**：将源图片中的人脸替换到目标图片中
  - **面部增强**：提升人脸图片的清晰度和质量
  - **替换+增强组合**：一步完成替换和增强操作
- 支持选择源图片中特定索引的人脸
- 自动识别并替换目标图片中最大的人脸
- 完全自包含设计，所有依赖和模型文件自动获取
- 通过API形式提供服务，方便前端页面调用

## 方式一：通过预构建Docker镜像快速部署

### 前提条件

- 安装Docker
- 确保服务器有足够的存储空间（至少15GB）
- 确保已开放需要的端口（默认为8001）

### 部署步骤

1. **克隆仓库获取配置文件**
   ```bash
   git clone https://github.com/Rsers/face-swap-docker.git
   cd face-swap-docker
   ```

2. **选择并下载预构建的Docker镜像文件**

   **选项A：从广州区域COS桶下载（中国大陆用户推荐）**
   ```bash
   # 安装COS命令行工具
   pip install coscmd
   
   # 配置COS访问凭证（连接到广州区域）
   ~/.local/bin/coscmd config -a YOUR_ACCESS_KEY_ID_HERE -s YOUR_ACCESS_KEY_SECRET_HERE -b face-swap-api-image-1259206939 -r ap-guangzhou
   
   # 下载Docker镜像文件（约10.8GB）
   ~/.local/bin/coscmd download /face-swap-api.tar ~/
   ```

   **选项B：从首尔区域COS桶下载（亚太地区用户推荐）**
   ```bash
   # 安装COS命令行工具
   pip install coscmd
   
   # 配置COS访问凭证（连接到首尔区域）
   ~/.local/bin/coscmd config -a YOUR_ACCESS_KEY_ID_HERE -s YOUR_ACCESS_KEY_SECRET_HERE -b docker-images-1259206939 -r ap-seoul
   
   # 下载Docker镜像文件（约10.8GB）
   ~/.local/bin/coscmd download /face-swap-api.tar ~/
   ```

3. **加载Docker镜像**
   ```bash
   docker load -i ~/face-swap-api.tar
   ```

4. **修改docker-compose.yml中的镜像名称**
   
   编辑docker-compose.yml文件，将image字段改为加载的镜像名称：
   ```bash
   # 查看加载的镜像名称
   docker images
   
   # 编辑docker-compose.yml文件
   nano docker-compose.yml
   ```
   
   将以下内容：
   ```yaml
   services:
     face-swap-api:
       build: .
   ```
   
   修改为（使用实际的镜像名和标签）：
   ```yaml
   services:
     face-swap-api:
       image: face-swap-docker_face-swap-api:latest
   ```

5. **启动服务**
   ```bash
   docker compose up -d
   ```

6. **验证服务是否正常运行**
   ```bash
   docker ps
   curl http://localhost:8001
   ```

## 方式二：通过源代码构建Docker镜像

### 前提条件

- 安装Docker和Docker Compose
- 确保服务器可访问互联网（首次部署需要下载模型文件）
- 推荐配置：2核CPU，4GB内存
- 确保已配置Git的用户名和邮箱（如果需要对项目进行修改和提交）

### 快速部署步骤

1. 克隆仓库到服务器
   ```bash
   git clone https://github.com/Rsers/face-swap-docker.git
   cd face-swap-docker
   ```

2. （可选）配置Git用户信息（如果尚未配置）
   ```bash
   git config --global user.name "您的名字"
   git config --global user.email "您的邮箱@example.com"
   ```

3. **重要**: 确保服务器防火墙已开放需要的端口（默认为8001，或您在docker-compose.yml中配置的其他端口）
   ```bash
   # 查看docker-compose.yml中配置的端口映射
   grep -E "ports:|[0-9]+:[0-9]+" docker-compose.yml
   
   # 对于使用ufw的系统（如Ubuntu）
   sudo ufw allow <您配置的端口>/tcp
   
   # 对于使用firewalld的系统（如CentOS）
   sudo firewall-cmd --permanent --add-port=<您配置的端口>/tcp
   sudo firewall-cmd --reload
   
   # 对于云服务器，还需要在云控制台的安全组/防火墙设置中开放对应端口
   ```

4. 一键启动服务
   ```bash
   docker compose up -d
   ```

5. 服务启动后，API将在以下地址可用：
   ```
   http://你的服务器IP:<您配置的端口>
   ```

首次启动时，系统会自动：
- 构建Docker镜像
- 从GitHub Releases下载所需的大型模型文件
- 配置持久化存储
- 启动所有API服务

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

#### 2. 面部增强接口

- URL: `/enhance_face`
- 方法: `POST`
- 参数:
  - `image`: (文件) 需要增强的图片
  - `output_name`: (可选) 输出文件名

- 返回:
  - `result_url`: 结果图片URL
  - `message`: 处理结果信息

#### 3. 面部替换与增强组合接口

- URL: `/face_swap_and_enhance`
- 方法: `POST`
- 参数:
  - `source_image`: (文件) 源图片，包含要提取的面部
  - `target_image`: (文件) 目标图片，将被替换面部
  - `output_name`: (可选) 输出文件名
  - `face_index`: (默认0) 使用源图像中的第几个人脸

- 返回:
  - `result_url`: 结果图片URL
  - `message`: 处理结果信息

#### 4. 获取图像接口

- URL: `/image/{image_path}`
- 方法: `GET`
- 参数:
  - `image_path`: 图像路径

#### 5. API信息接口

- URL: `/`
- 方法: `GET`
- 返回: API服务信息和可用端点

## 示例调用

### 面部替换示例

```bash
curl -X POST "http://localhost:8001/face_swap" \
  -F "source_image=@/path/to/source.jpg" \
  -F "target_image=@/path/to/target.jpg" \
  -F "output_name=swapped_result" \
  -F "face_index=0"
```

### 面部增强示例

```bash
curl -X POST "http://localhost:8001/enhance_face" \
  -F "image=@/path/to/image.jpg" \
  -F "output_name=enhanced_result"
```

### 面部替换与增强组合示例

```bash
curl -X POST "http://localhost:8001/face_swap_and_enhance" \
  -F "source_image=@/path/to/source.jpg" \
  -F "target_image=@/path/to/target.jpg" \
  -F "output_name=enhanced_swapped_result" \
  -F "face_index=0"
```

### Python调用示例

```python
import requests

def swap_and_enhance(source_path, target_path, output_name="enhanced_swap"):
    url = "http://localhost:8001/face_swap_and_enhance"
    
    files = {
        'source_image': open(source_path, 'rb'),
        'target_image': open(target_path, 'rb')
    }
    data = {
        'output_name': output_name
    }
    
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"处理成功！结果URL: {result['result_url']}")
        return result['result_url']
    else:
        print(f"错误: {response.text}")
        return None

# 使用示例
result_url = swap_and_enhance("source.jpg", "target.jpg", "my_result")
```

## 腾讯云COS桶操作指南

使用腾讯云对象存储服务(COS)能够方便地上传和下载Docker镜像文件，特别适合处理大型文件的快速传输和备份。

### 准备工作

1. 安装和更新COS命令行工具
   ```bash
   pip install coscmd && pip install coscmd -U && ~/.local/bin/coscmd -v
   ```

### 配置COS访问

2. 配置COS访问凭证
   ```bash
   # 配置韩国首尔区域的存储桶
   ~/.local/bin/coscmd config -a YOUR_ACCESS_KEY_ID_HERE -s YOUR_ACCESS_KEY_SECRET_HERE -b docker-images-1259206939 -r ap-seoul

   # 或配置广州区域的存储桶
   ~/.local/bin/coscmd config -a YOUR_ACCESS_KEY_ID_HERE -s YOUR_ACCESS_KEY_SECRET_HERE -b guangzhou-images-1259206939 -r ap-guangzhou
   ```

### 上传Docker镜像到COS

3. 使用以下脚本自动完成配置和上传过程
   ```bash
   AKID="YOUR_ACCESS_KEY_ID_HERE"
   AKS="YOUR_ACCESS_KEY_SECRET_HERE"
   BUCKET="docker-images-1259206939"
   REGION="ap-seoul"
   
   if [ ! -f "/home/ubuntu/.cos.conf" ]; then
     echo "配置文件 /home/ubuntu/.cos.conf 未找到，正在生成..."
     ~/.local/bin/coscmd config -a "$AKID" -s "$AKS" -b "$BUCKET" -r "$REGION"
     if [ $? -eq 0 ]; then
       echo "配置文件 /home/ubuntu/.cos.conf 生成成功。"
     else
       echo "配置文件生成失败，请检查 coscmd 是否正确安装。"
       exit 1
     fi
   else
     echo "配置文件 /home/ubuntu/.cos.conf 已存在。"
   fi
   
   read -p "请输入上传文件的绝对路径 (例如 /home/ubuntu/face-swap-api.tar): " UPLOAD_FILE_PATH
   COS_BUCKET_PATH="/"
   
   ~/.local/bin/coscmd upload --skipmd5 "$UPLOAD_FILE_PATH" "$COS_BUCKET_PATH"
   
   if [ $? -eq 0 ]; then
     echo "文件上传成功！"
     echo "上传文件路径: $UPLOAD_FILE_PATH"
     echo "COS 存储桶路径: $COS_BUCKET_PATH"
     file_size=$(du -h "$UPLOAD_FILE_PATH" | awk '{print $1}')
     echo "文件大小: $file_size"
   else
     echo "文件上传失败！请检查路径和 coscmd 配置。"
   fi
   ```

4. 也可以直接使用命令行上传（推荐方式）
   ```bash
   # 配置COS访问
   ~/.local/bin/coscmd config -a YOUR_ACCESS_KEY_ID_HERE -s YOUR_ACCESS_KEY_SECRET_HERE -b docker-images-1259206939 -r ap-seoul
   
   # 直接上传文件到COS桶根目录
   ~/.local/bin/coscmd upload --skipmd5 /home/ubuntu/face-swap-api.tar /
   
   # 上传大型文件时使用非后台模式可以查看上传进度
   # 对于10.8GB的Docker镜像，上传速度可达90MB/s以上，仅需约2分钟即可完成
   ```

### 从COS下载Docker镜像

5. 从广州区域COS桶下载Docker镜像文件
   ```bash
   # 配置COSCMD连接到广州区域的存储桶
   ~/.local/bin/coscmd config -a YOUR_ACCESS_KEY_ID_HERE -s YOUR_ACCESS_KEY_SECRET_HERE -b guangzhou-images-1259206939 -r ap-guangzhou
   
   # 下载Docker镜像文件
   ~/.local/bin/coscmd download /face-swap-api.tar ~/
   
   # 验证下载的文件大小
   du -h ~/face-swap-api.tar
   
   # 加载Docker镜像
   docker load -i ~/face-swap-api.tar
   ```

### 使用COS加速Docker镜像分发流程

使用腾讯云COS可以有效解决以下场景的问题：
- 在网络条件较差的环境中上传/下载大型Docker镜像
- 实现Docker镜像的备份与版本管理
- 在不同服务器之间快速迁移Docker镜像
- 将本地构建的Docker镜像分发到多个服务器

**注意事项**:
1. 上传大型文件时使用`--skipmd5`参数可以提高传输速度
2. 对于10GB以上的大型Docker镜像，建议检查COS桶的存储空间和流量费用
3. 传输完成后，可使用`docker load -i [文件路径]`加载镜像到Docker环境

## 技术细节与优化

- **模型文件管理**：所有大型模型文件从GitHub Releases自动下载，不需要手动操作
- **数据持久化**：使用Docker卷存储模型文件和处理结果，确保容器重启后数据不丢失
- **资源管理**：配置了合理的CPU和内存限制，避免服务占用过多系统资源
- **自动健康检查**：内置健康检查机制，确保服务稳定运行

## 注意事项

1. 首次部署时需要下载约1.3GB的模型文件，请确保网络连接稳定
2. 建议使用具有较高CPU性能的服务器以获得更好的处理速度
3. 默认使用CPU进行推理，如需使用GPU，请修改Dockerfile中的provider配置
4. 所有处理结果存储在`static/images/results`目录，可根据需要定期清理

## 常见问题与解决方案

在部署过程中可能会遇到以下问题，以下是解决方案：

### 0. Docker与Docker Compose的安装

**问题描述**：
系统可能没有安装Docker或Docker Compose，导致无法执行部署命令。

**解决方案**：
1. 安装Docker (如果尚未安装):
```bash
# 更新apt软件包索引
sudo apt update

# 安装必要的依赖
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# 添加Docker软件源
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# 更新apt包索引
sudo apt update

# 安装Docker CE
sudo apt install -y docker-ce
```

2. 安装Docker Compose (如果尚未安装):
```bash
# 安装Docker Compose
sudo apt install -y docker-compose

# 验证安装
docker-compose --version
```

3. 确保当前用户可以不使用sudo运行docker命令：
```bash
# 将当前用户添加到docker组
sudo usermod -aG docker $USER
# 注意：需要重新登录才能生效
```

### 1. Docker Compose 版本兼容性问题

**问题描述**：
在某些Docker Compose旧版本中(如1.25.0)，`docker-compose.yml`中的`healthcheck`配置中的`start_period`参数不被支持。

**错误信息**：
```
ERROR: The Compose file './docker-compose.yml' is invalid because:
services.face-swap-api.healthcheck value Additional properties are not allowed ('start_period' was unexpected)
```

**解决方案**：
修改`docker-compose.yml`文件，删除`healthcheck`中的`start_period`参数：

```yaml
healthcheck:
  test: [ "CMD", "curl", "-f", "http://localhost:8000/" ]
  interval: 30s
  timeout: 10s
  retries: 3
  # 移除 start_period 参数
```

### 2. 缺少Python依赖导致服务启动失败

**问题描述**：
服务启动时报错，提示缺少`basicsr`模块，这是GFPGAN库的依赖。

**错误信息**：
```
ModuleNotFoundError: No module named 'basicsr'
```

**解决方案**：
修改Dockerfile，显式安装`basicsr`库：
```dockerfile
# 安装缺失的basicsr依赖
RUN pip install --no-cache-dir basicsr
```

### 3. Torchvision版本兼容性问题

**问题描述**：
安装`basicsr`后，服务尝试启动时报错，显示找不到某些torchvision模块。

**错误信息**：
```
ModuleNotFoundError: No module named 'torchvision.transforms.functional_tensor'
```

**解决方案**：
需要安装特定版本的torchvision以确保兼容性。在Dockerfile中添加：
```dockerfile
# 安装特定版本的torchvision和basicsr以确保兼容性
RUN pip uninstall -y torchvision && \
    pip install --no-cache-dir torchvision==0.11.3 && \
    pip install --no-cache-dir basicsr
```

### 4. 首次部署时间较长

**问题描述**：
首次部署时，Docker构建过程可能需要很长时间，并且在下载模型文件时可能看不到明显的进度。

**解决方案**：
请耐心等待，首次部署需要下载约1.3GB的模型文件。你可以通过以下命令查看下载进度：
```bash
sudo docker-compose logs --follow
```

### 5. Docker权限问题

**问题描述**：
执行docker-compose命令时报错，提示没有足够权限，例如出现：
```
ERROR: Couldn't connect to Docker daemon at http+docker://localhost - is it running?
If it's at a non-standard location, specify the URL with the DOCKER_HOST environment variable.
```

**解决方案**：
临时解决方法是使用sudo执行命令：
```bash
sudo docker-compose up -d
```

永久解决方法是将当前用户添加到docker组（需要重新登录生效）：
```bash
sudo usermod -aG docker $USER
```

部署成功后，可以通过访问`http://服务器IP:8001`确认API服务是否正常运行。

### 6. Docker Compose环境变量警告

**问题描述**：
使用Docker Compose部署时可能会看到以下警告：
```
WARNING: The HOST_PORT variable is not set. Defaulting to a blank string.
WARNING: Some services (face-swap-api) use the 'deploy' key, which will be ignored. Compose does not support 'deploy' configuration - use `docker stack deploy` to deploy to a swarm.
```

**解决方案**：
这些警告通常不会影响服务的正常运行：
1. HOST_PORT警告是因为环境变量未设置，但docker-compose.yml中已有配置，可以忽略。
2. deploy配置警告是因为标准Docker Compose不支持deploy配置项，只有在Swarm模式下才支持。对于单机部署，该警告可以安全忽略。

### 7. API调用测试示例与响应解释

**测试命令**：
以下是一个完整的API调用测试示例，使用curl发送请求到`face_swap_and_enhance`接口：

```bash
curl -v -X POST "http://localhost:8001/face_swap_and_enhance" \
  -F "source_image=@/home/ubuntu/face-swap-docker/static/images/source.jpg" \
  -F "target_image=@/home/ubuntu/face-swap-docker/static/images/target.jpg" \
  -F "output_name=enhanced_swapped_result" \
  -F "face_index=0"
```

**成功响应示例**：
```json
{
  "result_url": "http://localhost:8001/image/results/enhanced_swapped_result.jpg",
  "message": "面部替换和增强成功! 面部交换成功 (使用第 1 个面部 (共检测到 3 个)，替换目标图像中唯一的人脸)，并且已进行面部增强处理"
}
```

**响应解释**：
- `result_url`: 处理后的图片访问地址
- `message`: 包含处理详情，如本例中源图片检测到3个人脸，使用了第1个人脸(索引从0开始)，目标图片中检测到1个人脸并已替换，最后进行了增强处理

**结果验证**：
处理后的图片会保存在服务器的以下位置：
```
/home/ubuntu/face-swap-docker/static/images/results/enhanced_swapped_result.jpg
```

可以通过浏览器访问`result_url`查看处理结果，或使用以下命令确认文件是否成功生成：
```bash
ls -la /home/ubuntu/face-swap-docker/static/images/results/enhanced_swapped_result.jpg
```

### 8. Git用户名和邮箱配置问题

**问题描述**：
在进行克隆或操作Git仓库时，可能会遇到以下错误信息：
```
请确保已在 Git 中配置你的 "user.name" 和 "user.email"。
```

**解决方案**：
这是因为Git需要知道提交代码的用户身份。可以通过以下命令设置Git的全局用户名和邮箱：
```bash
git config --global user.name "aaaa"
git config --global user.email "xxx@xxx.com"
```

您可以将上面的用户名和邮箱替换为您自己的信息。设置完成后，Git将使用这些信息来标识您的提交。