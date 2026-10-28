# تصویر پایه و ایندکس PyPI قابل تغییرند تا در شبکه‌هایی که Docker Hub / PyPI
# محدود است، از میرور استفاده شود. مقادیر پیش‌فرض برای شبکهٔ ایران تنظیم شده‌اند؛
# بیرون از ایران:  --build-arg PYTHON_IMAGE=python:3.12-slim --build-arg PIP_INDEX_URL=https://pypi.org/simple
ARG PYTHON_IMAGE=docker.arvancloud.ir/library/python:3.12-slim
FROM ${PYTHON_IMAGE}

ARG PIP_INDEX_URL=https://mirror-pypi.runflare.com/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir --index-url ${PIP_INDEX_URL} -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
