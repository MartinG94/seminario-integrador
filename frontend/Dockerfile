# ==============================================================================
# Dockerfile — Frontend Angular 14 (SGD-AVEIT)
# ==============================================================================
FROM node:18-bullseye-slim

WORKDIR /app

# Instalar Angular CLI globalmente con la versión oficial del proyecto
RUN npm install -g @angular/cli@14.2.7

# Copiar manifiestos de dependencias primero para optimizar capas de caché de Docker
COPY package.json package-lock.json* ./

# Instalar dependencias con compatibilidad para Material Dashboard PRO
RUN npm install --legacy-peer-deps

# Copiar el código fuente completo del frontend
COPY . .

# Exponer el puerto estándar de desarrollo de Angular
EXPOSE 4200

# Iniciar servidor con bind a todas las interfaces y polling para sincronización de volúmenes
CMD ["npm", "start", "--", "--host", "0.0.0.0", "--port", "4200", "--poll", "2000"]
