from ultralytics import YOLO
import torch

# clase: 1 License_Plate
# Load a model
#model = YOLO('yolov8n.pt')  # load a pretrained model (recommended for training)
#model = YOLO('.\models\license_plate_detector.pt')

# Train the model
#results = model.train(data='.\datasets\LicensePlateRecognition\data.yaml', epochs=10, imgsz=640, device='cpu', cache='disk', pretrained=True)
#results = model.train(data='.\datasets\license_ocr.v3i.yolov8\data.yaml', epochs=10, imgsz=640, device='cpu', cache='disk', pretrained=True, plots=True)


import os
import json

def create_json_files_for_each_file(directory):
    # Comprueba si la ruta proporcionada es una carpeta
    if not os.path.isdir(directory):
        print(f"{directory} no es una carpeta válida.")
        return

    # Recorre todos los archivos en la carpeta
    for filename in os.listdir(directory):
        # Construye la ruta completa del archivo
        file_path = os.path.join(directory, filename)

        # Si es un archivo (no una carpeta)
        if os.path.isfile(file_path):
            # Obtén el nombre del archivo sin extensión
            base_name, _ = os.path.splitext(filename)

            # Construye la ruta completa del archivo .json a crear
            json_file_path = os.path.join(directory, base_name + '.json')

            # Crea el archivo .json con el campo 'license_plate'
            data = {
                "license_plate": ""
            }
            with open(json_file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

            print(f"Archivo {json_file_path} creado.")

# Ejemplo de uso
carpeta = ".\\datasets\\baza_slika\\040603"  # Reemplaza esto con la ruta a tu carpeta
create_json_files_for_each_file(carpeta)
