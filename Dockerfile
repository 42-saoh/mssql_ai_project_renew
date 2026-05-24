FROM python:3.12-slim
WORKDIR /workspace
COPY requirements-dev.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
ENV PYTHONPATH=/workspace:/workspace/packages/contracts/src:/workspace/packages/orchestration/src:/workspace/packages/validation/src:/workspace/services/codex-runner
