# ==============================================================================
# Dockerfile — Backend Django 4.2+ (Python 3.12 / SGD-AVEIT)
# ==============================================================================
FROM python:3.12-slim-bookworm

# Evitar buffering de salida de stdout/stderr y escritura de archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar mysqlclient contra MySQL 8
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar manifiesto de dependencias e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente completo del backend
COPY . .

# Exponer el puerto del servidor de desarrollo Django
EXPOSE 8000

# Iniciar servidor de desarrollo enlazando a todas las interfaces
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
