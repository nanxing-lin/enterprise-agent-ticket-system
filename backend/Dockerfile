# 使用 Python 3.10 轻量级镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖清单并安装（先装依赖，利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制整个后端代码
COPY . .

# 暴露端口
EXPOSE 8002

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]