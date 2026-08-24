FROM python:3.12-slim AS runtime

ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app
COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --upgrade pip \
    && python -c 'import subprocess, sys, tomllib; config = tomllib.load(open("pyproject.toml", "rb")); requirements = config["build-system"]["requires"] + config["project"]["dependencies"]; subprocess.check_call([sys.executable, "-m", "pip", "install", *requirements])'

COPY backend/app ./app
RUN pip install --no-deps --no-build-isolation .

COPY knowledge /knowledge
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
