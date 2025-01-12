import os
import requests
import time
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException

# Configuración de Selenium
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Crear las carpetas de descarga si no existen
os.makedirs('imagenes_descargadas', exist_ok=True)
os.makedirs('videos_descargados', exist_ok=True)

# Registros de URLs ya descargadas
imagenes_descargadas = set()
videos_descargados = set()

# Función para previsualizar la resolución de la imagen
def obtener_resolucion_imagen(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image.size  # Retorna (ancho, alto)
    except Exception as e:
        print(f"No se pudo obtener la resolución de la imagen: {e}")
        return None

# Función para descargar imágenes o videos
def descargar_archivo(url, tipo, nombre):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        if tipo == 'imagen':
            with open(f"imagenes_descargadas/{nombre}", 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Imagen descargada como: {nombre}")
        elif tipo == 'video':
            with open(f"videos_descargados/{nombre}", 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Video descargado como: {nombre}")
    except Exception as e:
        print(f"Error al descargar el archivo: {e}")

# Función para examinar y procesar imágenes y videos
def examinar_y_descargar():
    global imagenes_descargadas, videos_descargados

    try:
        # Buscar imágenes
        imagenes = driver.find_elements(By.TAG_NAME, 'img')
        for index, img in enumerate(imagenes):
            try:
                img_url = img.get_attribute('src')
                if img_url and not img_url.startswith("data:") and img_url not in imagenes_descargadas:
                    resumen_url = img_url[:50] + "..." if len(img_url) > 50 else img_url
                    # Obtener resolución de la imagen
                    resolucion = obtener_resolucion_imagen(img_url)
                    if resolucion:
                        print(f"Imagen detectada {index + 1}: {resumen_url} (Resolución: {resolucion[0]}x{resolucion[1]})")
                    else:
                        print(f"Imagen detectada {index + 1}: {resumen_url} (Resolución desconocida)")

                    # Preguntar al usuario si desea descargarla
                    try:
                        respuesta = input("¿Quieres descargarla? (s/n): ")
                    except Exception as e:
                        print(f"Error al capturar la respuesta del usuario: {e}")
                        respuesta = "n"  # Asumir "no" si ocurre un error
                        
                    if respuesta.lower() == 's':
                        nombre_archivo = img_url.split("/")[-1].split("?")[0]  # Extraer el nombre del archivo
                        descargar_archivo(img_url, 'imagen', nombre_archivo)
                        imagenes_descargadas.add(img_url)
                    else:
                        print("************************* Imagen omitida.")
            except StaleElementReferenceException:
                print("Elemento de imagen obsoleto. Saltando...")

        # Buscar videos
        videos = driver.find_elements(By.TAG_NAME, 'video')
        for index, video in enumerate(videos):
            try:
                video_url = video.get_attribute('src')
                if video_url and not video_url.startswith("blob:") and video_url not in videos_descargados:
                    resumen_url = video_url[:50] + "..." if len(video_url) > 50 else video_url
                    print(f"Video detectado {index + 1}: {resumen_url}")
                    try:
                        respuesta = input("¿Quieres descargarlo? (s/n): ")
                    except Exception as e:
                        print(f"Error al capturar la respuesta del usuario: {e}")
                        respuesta = "n"  # Asumir "no" si ocurre un error
                        
                    if respuesta.lower() == 's':
                        nombre_archivo = video_url.split("/")[-1].split("?")[0]  # Extraer el nombre del archivo
                        descargar_archivo(video_url, 'video', nombre_archivo)
                        videos_descargados.add(video_url)
                    else:
                        print("************************* Video omitido.")
                elif video_url and video_url.startswith("blob:"):
                    print(f"************************* URL de video no descargable: {video_url}")
            except StaleElementReferenceException:
                print("Elemento de video obsoleto. Saltando...")

    except Exception as e:
        print(f"Error durante la exploración: {e}")

# Navegar a la página inicial
driver.get("https://www.google.com/")

# Esperar un tiempo para que cargue la página
time.sleep(5)

# Procesar la página actual
examinar_y_descargar()

# Loop principal para actualizar y detectar cambios
contenido_anterior = set()  # Para comparar el contenido antes y después de actualizar

try:
    while True:
        # Extraer URLs actuales (imágenes y videos)
        contenido_actual = set()

        # Agregar imágenes detectadas
        imagenes = driver.find_elements(By.TAG_NAME, 'img')
        for img in imagenes:
            try:
                img_url = img.get_attribute('src')
                if img_url and not img_url.startswith("data:"):
                    contenido_actual.add(img_url)
            except StaleElementReferenceException:
                pass

        # Agregar videos detectados
        videos = driver.find_elements(By.TAG_NAME, 'video')
        for video in videos:
            try:
                video_url = video.get_attribute('src')
                if video_url:
                    contenido_actual.add(video_url)
            except StaleElementReferenceException:
                pass

        # Comparar con contenido anterior
        nuevo_contenido = contenido_actual - contenido_anterior
        if nuevo_contenido:
            print("****************************************************")
            print(f"Nuevo contenido detectado: {len(nuevo_contenido)} elementos nuevos.")
            contenido_anterior = contenido_actual  # Actualizar el contenido procesado

            # Examinar y procesar el nuevo contenido
            examinar_y_descargar()
        else:
            print("No se detectó contenido nuevo. Validando...")

        # Actualizar la página y esperar antes de volver a procesar
        driver.refresh()
        time.sleep(10)

except KeyboardInterrupt:
    print("Detenido por el usuario.")
finally:
    driver.quit()
