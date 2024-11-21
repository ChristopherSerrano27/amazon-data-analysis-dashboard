# Usar la imagen base de Python 3.12
FROM python:3.12.7-slim

# Configurar el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos necesarios
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto en el que corre la app (ajusta según tu configuración)
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
