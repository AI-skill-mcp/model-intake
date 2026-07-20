# 默认走 DaoCloud 代理，避免直连 Docker Hub 超时；可通过 --build-arg 覆盖
ARG PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.12-slim
FROM ${PYTHON_IMAGE}
WORKDIR /app
COPY docker/etl/requirements.txt ./requirements.txt
# PyPI 走清华源，降低国内构建时拉包失败概率
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt
COPY etl/ ./etl/
ENV PYTHONPATH=/app
CMD ["python", "-m", "etl.run"]
