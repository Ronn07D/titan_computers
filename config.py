import os
from dotenv import load_dotenv, find_dotenv

# find_dotenv() busca el .env hacia arriba en las carpetas
dotenv_path = find_dotenv() 
print(f"--> Cargando .env desde: {dotenv_path}")

# verbose=True imprimirá en consola si lo encontró o no
load_dotenv(dotenv_path, verbose=True) 

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    
    # Verificación de seguridad: Si falta alguna, lanza un error claro
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        raise ValueError(f"Faltan variables de entorno. Revisa tu archivo .env. Valores actuales: User={DB_USER}, Host={DB_HOST}, Name={DB_NAME}")

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #define la ruta donde se guardaran las imagenes de los productos
    UPLOAD_FOLDER = os.path.join('app', 'static', 'img', 'productos')
    