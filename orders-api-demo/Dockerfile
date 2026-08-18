FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /srv

COPY pyproject.toml ./
RUN uv sync --no-install-project

COPY . .
RUN uv sync

ENV PATH="/srv/.venv/bin:${PATH}"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
