# 使用轻量级 Nginx 镜像
FROM nginx:alpine

# 把打包好的静态文件拷进 Nginx 目录
COPY dist /usr/share/nginx/html

# 把我们写的 Nginx 配置覆盖默认配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]