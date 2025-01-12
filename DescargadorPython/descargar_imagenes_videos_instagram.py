import os
import time
import requests
from instagrapi import Client

# Crear instancia del cliente
client = Client()

# Iniciar sesión
print("Iniciando sesión en Instagram...")
username = "usuario"  # Reemplaza con tu usuario de Instagram
password = "contraseña"  # Reemplaza con tu contraseña
client.login(username, password)
print("Inicio de sesión exitoso.")

# Función para crear carpetas organizadas por usuario
def crear_carpetas(base_path, usuario):
    usuario_path = os.path.join(base_path, usuario)
    carpetas = {
        "perfil": os.path.join(usuario_path, "foto_perfil"),
        "publicaciones": os.path.join(usuario_path, "publicaciones"),
        "historias": os.path.join(usuario_path, "historias"),
        "destacados": os.path.join(usuario_path, "destacados"),
    }
    for carpeta in carpetas.values():
        os.makedirs(carpeta, exist_ok=True)
    return carpetas

# Descargar la foto de perfil manualmente
def descargar_foto_perfil(usuario, carpeta_destino):
    print("Descargando foto de perfil...")
    perfil = client.user_info_by_username(usuario)  # Obtiene la información del usuario
    foto_url = perfil.profile_pic_url_hd  # URL de la foto de perfil en alta resolución

    # Descargar la foto
    response = requests.get(foto_url, stream=True)
    if response.status_code == 200:
        ruta_archivo = os.path.join(carpeta_destino, "foto_perfil.jpg")
        with open(ruta_archivo, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Foto de perfil descargada en: {ruta_archivo}")
    else:
        print("No se pudo descargar la foto de perfil.")

# Descargar publicaciones, historias y destacados
def descargar_todo_perfil(usuario):
    base_path = "descargas_instagram"
    carpetas = crear_carpetas(base_path, usuario)
    
    print(f"\nDescargando contenido para el usuario: {usuario}")
    user_id = client.user_id_from_username(usuario)

    # Descargar la foto de perfil
    descargar_foto_perfil(usuario, carpetas["perfil"])

    # Descargar publicaciones
    print("Descargando publicaciones...")
    publicaciones = client.user_medias(user_id, amount=50)  # Cambia el número según sea necesario
    for media in publicaciones:
        try:
            if media.media_type == 1:  # Foto
                foto_path = client.photo_download(media.pk, folder=carpetas["publicaciones"])
                print(f"Foto descargada: {foto_path}")
            elif media.media_type == 2:  # Video
                video_path = client.video_download(media.pk, folder=carpetas["publicaciones"])
                print(f"Video descargado: {video_path}")
        except Exception as e:
            print(f"Error al descargar publicación {media.pk}: {e}")
        time.sleep(2)

    # Descargar historias activas
    print("Descargando historias activas...")
    historias = client.user_stories(user_id)
    for historia in historias:
        try:
            if historia.video_url:
                video_path = client.story_download(historia.pk, folder=carpetas["historias"])
                print(f"Historia (video) descargada: {video_path}")
            elif historia.thumbnail_url:
                imagen_path = client.photo_download(historia.pk, folder=carpetas["historias"])
                print(f"Historia (imagen) descargada: {imagen_path}")
        except Exception as e:
            print(f"Error al descargar historia {historia.pk}: {e}")
        time.sleep(2)

    # Descargar historias destacadas
    print("Descargando historias destacadas...")
    destacados = client.user_highlights(user_id)
    for destacado in destacados:
        print(f"Descargando historias de destacados: {destacado.title}")
        for item in destacado.items:
            try:
                if item.video_url:
                    video_path = client.story_download(item.pk, folder=os.path.join(carpetas["destacados"], destacado.title))
                    print(f"Destacado (video) descargado: {video_path}")
                elif item.thumbnail_url:
                    imagen_path = client.photo_download(item.pk, folder=os.path.join(carpetas["destacados"], destacado.title))
                    print(f"Destacado (imagen) descargada: {imagen_path}")
            except Exception as e:
                print(f"Error al descargar destacado {item.pk}: {e}")
            time.sleep(2)

    print(f"\nDescarga completa para el usuario: {usuario}")

# Pedir al usuario el nombre de usuario o enlace
usuario_input = input("Ingresa el nombre de usuario o enlace del perfil: ").strip()

# Extraer el nombre de usuario del enlace si es necesario
if "instagram.com" in usuario_input:
    usuario_input = usuario_input.split("/")[-2]  # Extrae el nombre del usuario del enlace

# Descargar el perfil
try:
    descargar_todo_perfil(usuario_input)
except Exception as e:
    print(f"Error al descargar contenido de {usuario_input}: {e}")
