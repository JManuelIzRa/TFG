import cv2
from ultralytics import YOLO
import cv2

from util import get_car, read_license_plate, write_csv
import numpy as np
import re

import os
import glob
import torch
from easyocr import Reader
from ultralytics.utils.plotting import Annotator
import threading
import concurrent.futures

import requests

import aiohttp
import asyncio

import threading
import time
import queue


#from paddleocr import PaddleOCR,draw_ocr

from flask import Flask, jsonify

import re
from matplotlib import pyplot as plt

semaforo = threading.Semaphore(1) #Crear variable semáforo
# Crea un evento para señalar cuando la hebra debe terminar
stop_event = threading.Event()

send_images_event = threading.Event()
client_mode_entry = threading.Event()

app = Flask(__name__)

@app.route('/start-sending-frames', methods=['GET'])
def start_sending_images():
    
    send_images_event.set()
    
    return jsonify({'status': 'started'})


@app.route('/stop-sending-images', methods=['GET','POST'])
def stop_sending_images():
        
    send_images_event.clear()

    return jsonify({'status': 'stopped'})

@app.route('/configurate-camera/entry', methods=['GET','POST'])
def configurate_camera_entry():
        
    client_mode_entry.set()

    return jsonify({'status': 'Entry Camera'})

@app.route('/configurate-camera/exit', methods=['GET','POST'])
def configurate_camera_exit():
    client_mode_entry.clear()

    return jsonify({'status': 'Exit Camera'})



def load_models():
    # load models
    coco_model = YOLO('yolov8n.pt')
    coco_model.to('cpu')

    license_plate_detector = YOLO('./models/license_plate_detector.pt')
    license_plate_detector.to('cpu')

    ocr_model = YOLO('./models/ocr.pt')
    ocr_model.to('cpu')


    paht_predicciones = ".\\runs\\detect\\predict4"

    return coco_model, license_plate_detector, ocr_model, paht_predicciones

def resize_image_to_dpi(image, dpi=300):
    # Calculate the target width and height for the desired DPI
    width_inch = image.shape[1] / dpi
    height_inch = image.shape[0] / dpi
    target_width = int(width_inch * 300)  # 300 DPI
    target_height = int(height_inch * 300)  # 300 DPI

    # Resize the image to the calculated dimensions
    resized_image = cv2.resize(image, (target_width, target_height))
    return resized_image

def apply_adaptive_threshold(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresholded = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresholded

def apply_otsu_binarization(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresholded

def remove_noise(image):
    denoised = cv2.GaussianBlur(image, (5, 5), 0)
    return denoised

def apply_morphology(image):
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(image, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    return eroded

def deskew_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = contours[0]
    angle = cv2.minAreaRect(contour)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    rotated = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return rotated

def add_border(image, border_size=10, white=True):
    # Verificar si la imagen es en escala de grises
    if len(image.shape) == 2:
        # Convertir la imagen en escala de grises a una imagen en color (escala de grises replicada en cada canal)
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    if white:
        # Agregar un borde blanco a la imagen en color
        bordered = cv2.copyMakeBorder(image, border_size, border_size, border_size, border_size, 
                                    cv2.BORDER_CONSTANT, value=(255, 255, 255))  # White border
    else:
        bordered = cv2.copyMakeBorder(image, border_size, border_size, border_size, border_size, 
                                    cv2.BORDER_CONSTANT, value=(0, 0, 0))  # Black border
    
    target_height = image.shape[0]
    target_width = image.shape[1]
    resized_image = cv2.resize(bordered, (target_width, target_height))
    
    return resized_image


# Función para convertir una imagen en escala de grises a color
def gray_to_color(image):
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image



def detect_horizontal_lines(image, original_image):

    result_image = original_image.copy()

    # Convertir la imagen a escala de grises si es necesario
    if len(image.shape) > 2 and image.shape[2] > 1:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image  # La imagen ya es una escala de grises
    
    # Aplicar suavizado para reducir el ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detectar bordes usando Canny
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
    
    # Aplicar transformada de Hough para detectar líneas
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 60, 50, 10, maxLineGap=5)

    horizontal_lines = []

        # Filtrar líneas horizontales basadas en la pendiente
    if lines is None:
        print("No se detectaron líneas horizontales.")
        return [], None  # Devolver una lista vacía si no se detectaron líneas
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(y2 - y1) < 60 and abs(x2-x1) > 10:  # Considerar líneas casi horizontales (umbral ajustable)
            horizontal_lines.append(line)
            cv2.line(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Dibujar la línea sobre la imagen original

    
    return horizontal_lines, result_image

def calculate_angle_of_inclination(horizontal_lines):
    # Calcular el ángulo de inclinación promedio de las líneas horizontales
    angles = []
    for line in horizontal_lines:
        x1, y1, x2, y2 = line[0]

        # (y2-y1)/(x2-x1) es la forma de calcular la pendiente de la recta,
        # una vez calculada calculamos la arcotangente para obtener el angulo de inclinacion
        angle_rad = np.arctan2(y2 - y1, x2 - x1)
        angle_deg = np.degrees(angle_rad)
        angles.append(angle_deg)
    
    # Calcular el ángulo promedio
    if angles:
        average_angle = np.mean(angles)
    else:
        average_angle = 0.0
    
    return average_angle

def correct_perspective(image, angle_of_inclination):
    # Obtener dimensiones de la imagen
    h, w = image.shape[:2]
    
    # Calcular la matriz de transformación de perspectiva para enderezar la imagen
    rotation_matrix = cv2.getRotationMatrix2D((w // 2, h // 2), -angle_of_inclination, 1.0)
    corrected_image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    
    return corrected_image

def centered_license_plate(license_plate_ROI):

    license_plate = license_plate_ROI.copy()
    # Resize to minimum 300 DPI
    resized_image = resize_image_to_dpi(license_plate)

    # Apply adaptive thresholding
    #thresholded_image = apply_adaptive_threshold(resized_image)

    # Apply Otsu's binarization
    thresholded_image = apply_otsu_binarization(resized_image)

    # Remove noise
    denoised_image = remove_noise(thresholded_image)

    # Apply dilation and erosion
    processed_image = apply_morphology(denoised_image)

    # Rotate / Deskew the image
    #rotated_image = deskew_image(processed_image)
    
    # Calcula la mediana de la intensidad de los gradientes
    median_intensity = np.median(processed_image)
    
    # Define los umbrales bajo y alto adaptativos basados en la mediana
    lower_threshold = float(max(0, (1.0 - 0.33) * median_intensity))
    upper_threshold = float(min(255, (1.0 + 0.33) * median_intensity))
    
    # Aplica el detector de bordes Canny con los umbrales adaptativos
    edges = cv2.Canny(thresholded_image, lower_threshold, upper_threshold)
    # Detectar líneas horizontales en la placa de matrícula
    horizontal_lines, imagen_lineas_h = detect_horizontal_lines(edges, resized_image)

    # Calcular el ángulo de inclinación promedio de las líneas horizontales
    if np.size(horizontal_lines) != 0:

        angle_of_inclination = calculate_angle_of_inclination(horizontal_lines)

        # Corregir la perspectiva de la placa de matrícula basada en el ángulo de inclinación
        corrected_plate_image = correct_perspective(license_plate_ROI, -angle_of_inclination)
    else:
        corrected_plate_image = license_plate_ROI


    return corrected_plate_image

def cleanup_text(text):
	# strip out non-ASCII text so we can draw the text on the image
	# using OpenCV

    clean_text =  "".join([c if ord(c) < 128 else "" for c in text]).strip()

    # Usar una expresión regular para eliminar los caracteres no deseados
    clean_text = re.sub(r'[\[\]\-\s\.,;:!?"\'(){}<>]', '', clean_text)
    return clean_text


def calculate_bounds(roi):
    x, y, width, height = cv2.boundingRect(roi)
    x_min = x
    y_min = y
    x_max = x + width
    y_max = y + height
    return (x_min, y_min, x_max, y_max)


def is_roi_contained(roi_inner, roi_outer):
    x_min_inner, y_min_inner, x_max_inner, y_max_inner = calculate_bounds(roi_inner)
    x_min_outer, y_min_outer, x_max_outer, y_max_outer = calculate_bounds(roi_outer)

    # Comprobar si el ROI interno está completamente dentro del ROI externo
    return (x_min_inner >= x_min_outer and
            y_min_inner >= y_min_outer and
            x_max_inner <= x_max_outer and
            y_max_inner <= y_max_outer)

#def send_license_plate(session, plate_number):
def wait_license_plate(stop_event, send_images_event):
    
    while not stop_event.is_set():
        if not q.empty():
            semaforo.acquire()
            plate_number = q.get()
            send_license_plate(plate_number)
            q.task_done()
            semaforo.release()

        if (cv2.waitKey(1) == ord('s')):
            return

def send_license_plate(plate_number):
    
    if client_mode_entry.is_set() == True:
        url = 'http://localhost:8000/license_plate/api/register/'
    else:
        url = 'http://localhost:8000/license_plate/api/register_exit/'
    
    with open(f'./LPR_RealTime/media/{plate_number}.jpg', "rb") as image_file:

        data = {
            'plate_number': plate_number,
        }

        response = requests.post(url, data=data, files={"detection_image": image_file})

        if response.status_code == 201:
            print('Number plate sent correctly:', response.json())
        else:
            print('Error while sending numer plate:', response.status_code, response.text)

def wait_for_frame(stop_event, send_images_event):
    
    while not stop_event.is_set():

        if send_images_event.is_set():
            send_frame()
        
        if (cv2.waitKey(1) == ord('s')):
            return

def send_frame():
    url = "http://127.0.0.1:8000/cams/api/upload/"

    # Abre la imagen en modo binario
    with open("./LPR_RealTime/media/current_frame.jpg", "rb") as image_file:
        # Envía una solicitud POST con la imagen
        response = requests.post(url, files={"image": image_file})

    # Imprime la respuesta de la API
    #print(response.status_code)
    #print(response.json())


#def analizar_frame(frame):

# Función principal que captura frames y envía las solicitudes
#async def main():
def main_process(stop_event, send_images_event):
    # Crear una sesión de aiohttp
    #async with aiohttp.ClientSession() as session:

    capture = cv2.VideoCapture("./LPR_RealTime/demo.mp4")
    #capture = cv2.VideoCapture(0)

    license_plate_found = {}

    coco_model, license_plate_detector, ocr_model, paht_predicciones = load_models()

    ## Declaracion inicial easyocr
    reader = Reader(lang_list=["es"], gpu=True)

    results = {}

    # Supongamos que solo estamos interesados en las cajas delimitadoras con una confianza mayor que un umbral
    confianza_umbral = 0.5
    coordenadas_cajas = []

    #print(predictions)
    vehicles = [2,3,5,7]

    imagenes_recortadas = []

    threshold = 70

    index_file_predict = 0
    hilos = []

    while (capture.isOpened()):
        
        ret, frame = capture.read()
        cv2.imshow('webCam',frame)
        cv2.imwrite("./LPR_RealTime/media/current_frame.jpg", frame)

        # If the input is a video we check if it is the last frame
        if not ret:
            print("End of the video.")
            break


        if (cv2.waitKey(1) == ord('q')):
            stop_event.set()
            break

        q_frames.put(frame)
            
        #detections = coco_model(frame, verbose=True, classes=vehicles, conf=0.7)[0]
        detections = coco_model.predict(frame, verbose=False, classes=vehicles, conf=0.7, device='cpu')[0]
        detections_ = []

        detections = detections.boxes.data.tolist()

        best_detection = None

        best_car_detection = 0.0

        for detection in detections:
            x1, y1, x2, y2, score, class_id = detection

            if score > best_car_detection:
                
                best_detection = detection
                
                best_car_detection = score
                

        if best_detection == None:
            continue

        x1, y1, x2, y2, score, class_id = best_detection

        if int(class_id) in vehicles:
            
            image_crop = frame[int(y1):int(y2), int(x1): int(x2)]
            
            lp_predictions = license_plate_detector.predict(source=image_crop, verbose=False, device='cpu')[0]

            #lp_predictions.save(f'.//license_plate_predictions//img{index_file_predict}.jpg')
            cv2.imshow("Coche detectado", image_crop)

            best_score = 0

            for detection in lp_predictions.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = detection

                if score > best_score:

                    license_plate_ROI = image_crop[int(y1):int(y2),int(x1):int(x2)]

                    license_plate_ROI_save = license_plate_ROI.copy()

                    cv2.imshow("Placa detectada", license_plate_ROI)

                    best_score = score

                    thresholded_image = apply_otsu_binarization(license_plate_ROI_save)
                    gray=cv2.bilateralFilter(thresholded_image,11,17,17)
                    denoised_image = remove_noise(thresholded_image)
                    processed_image = apply_morphology(denoised_image)
                    
                    # Calcula la mediana de la intensidad de los gradientes
                    median_intensity = np.median(processed_image)
                        
                    # Define los umbrales bajo y alto adaptativos basados en la mediana
                    lower_threshold = float(max(0, (1.0 - 0.33) * median_intensity))
                    upper_threshold = float(min(255, (1.0 + 0.33) * median_intensity))
                        
                    # Aplica el detector de bordes Canny con los umbrales adaptativos
                    edges = cv2.Canny(thresholded_image, lower_threshold, upper_threshold) 
                    # Detectar líneas horizontales en la placa de matrícula
                    horizontal_lines, imagen_lineas_h = detect_horizontal_lines(edges, license_plate_ROI_save)

                    # Calcular el ángulo de inclinación promedio de las líneas horizontales
                    if np.size(horizontal_lines) != 0:

                        angle_of_inclination = calculate_angle_of_inclination(horizontal_lines)

                        # Corregir la perspectiva de la placa de matrícula basada en el ángulo de inclinación
                        corrected_plate_image = correct_perspective(license_plate_ROI, -angle_of_inclination)
                    else:
                        corrected_plate_image = license_plate_ROI

                    horizontal_license_plate = centered_license_plate(license_plate_ROI_save)

                    image = horizontal_license_plate.copy()

                    cv2.imshow("Placa horizontal", horizontal_license_plate)

                    #now we will convert image to gray scale
                    #why we do is because it will reduce the dimension , also reduces complexity of image
                    #and yeah there are few algorithms like canny , etc which only works on grayscale images
                    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
                    #gray=cv2.bilateralFilter(gray,11,17,17)
                    resize_image = cv2.resize(gray, None, fx = 3, fy= 3, interpolation = cv2.INTER_CUBIC)

                    #blured_image = cv2.GaussianBlur(resize_image, (5,5), 0)

                    ret, thresh = cv2.threshold(resize_image, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY)
                    rect_kern = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))

                    dilation = cv2.dilate(thresh, rect_kern, iterations = 1)
                    cv2.imshow("Placa dilation", resize_image)

                    ocr_results = reader.readtext(horizontal_license_plate)

                    for (bbox, text, prob) in ocr_results:
                        # display the OCR'd text and associated probability
                        print("[INFO] {:.4f}: {}".format(prob, text))

                        # cleanup the text and draw the box surrounding the text along
                        # with the OCR'd text itself
                        clean_text = cleanup_text(text)

                        print(clean_text)

                        if clean_text in license_plate_found.keys():
                            license_plate_found[clean_text] += 1
                        else:
                            license_plate_found[clean_text] = 1

                        if license_plate_found[clean_text] > 4:
                            print("The license plate has been found more than 4 times.")
                            cv2.imwrite(f'./LPR_RealTime/media/{clean_text}.jpg', license_plate_ROI)
                            q.put(clean_text)

    capture.release()
    cv2.destroyAllWindows()


def init_api(stop_event, send_images_event):
    app.run(port=8001, use_reloader=False)

if __name__ == '__main__':
    #asyncio.run(main())

    '''url = 'http://localhost:8000/cams/api/connect'
    
    data = {
        'parking':"Parking Central",
        'direction':"Entry",
        'is_active':True
    }

    response = requests.post(url, data=data)

    if response.status_code == 201:
        print('Camera connected successfully:', response.json())
    else:
        print('Error while connecting camera:', response.status_code, response.text)'''

    tareas = [main_process, wait_license_plate, init_api, wait_for_frame]

    threads = []
    event = threading.Event()
    q = queue.Queue() 

    q_frames = queue.Queue()

    for i, tarea in enumerate(tareas):
        threads.append(threading.Thread(target=tareas[i], args=(stop_event, send_images_event), name=f"Thread-{i}"))
        threads[i].start()

    for i in range(len(threads)):
        threads[i].join()
    
