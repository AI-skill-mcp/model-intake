# 默认走 DaoCloud 代理，避免直连 Docker Hub 超时；可通过 --build-arg 覆盖
ARG NODE_IMAGE=docker.m.daocloud.io/library/node:20-alpine
FROM ${NODE_IMAGE}
WORKDIR /app
COPY web/package.json web/package-lock.json* ./
# npm 走淘宝源，降低国内构建时拉包失败概率
RUN npm config set registry https://registry.npmmirror.com \
    && npm install
COPY web/ .
RUN mkdir -p public/data
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
