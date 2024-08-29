import csv
import os
import re
import numpy as np
from sklearn.metrics import accuracy_score
from Levenshtein import distance as levenshtein_distance

def preprocesar_texto(texto):
    # Eliminar los caracteres especiales
    texto = re.sub(r'[ªº\\!|\"@·#$%&/()=?¿\'¡`^[\]+*´{}_\-.,<>]', '', texto)
    # Convertir a mayúsculas
    texto = texto.upper()
    return texto

def leer_respuesta_correcta_txt(archivo_txt):
    # Leer cada línea del archivo y unirlas en una sola cadena
    with open(archivo_txt, 'r') as f:
        caracteres = f.read().splitlines()
    # Unir los caracteres y preprocesar
    matricula = ''.join(caracteres)
    return preprocesar_texto(matricula)

def leer_respuestas_correctas(carpeta_txt):
    respuestas_correctas = {}
    for archivo in os.listdir(carpeta_txt):
        if archivo.endswith('.txt'):
            archivo_path = os.path.join(carpeta_txt, archivo)
            respuestas_correctas[archivo] = leer_respuesta_correcta_txt(archivo_path)
    return respuestas_correctas

def leer_predicciones(csv_file):
    predicciones = []
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            predicciones.append([preprocesar_texto(pred) for pred in row])
    return predicciones

def al_menos_cuatro_coinciden(texto1, texto2):
    coincidencias = sum(1 for a, b in zip(texto1, texto2) if a == b)
    return coincidencias >= 4

def evaluar_modelos(predicciones, respuestas_correctas):
    resultados = []
    archivos_txt = list(respuestas_correctas.keys())

    for i, implementacion in enumerate(predicciones):
        y_true = []
        y_pred = []
        distancias_levenshtein = []
        coincidencias_min4 = []

        for j, prediccion in enumerate(implementacion):
            archivo_txt = archivos_txt[j]
            respuesta_correcta = respuestas_correctas[archivo_txt]
            y_true.append(respuesta_correcta)
            y_pred.append(prediccion)
            
            # Calcular distancia de Levenshtein
            distancia = levenshtein_distance(respuesta_correcta, prediccion)
            distancias_levenshtein.append(distancia)
            
            # Verificar si al menos 4 caracteres coinciden
            coincidencia = al_menos_cuatro_coinciden(respuesta_correcta, prediccion)
            coincidencias_min4.append(coincidencia)
        
        # Calcular precisión completa
        accuracy_completa = accuracy_score(y_true, y_pred)
        # Calcular la distancia promedio de Levenshtein
        distancia_promedio = np.mean(distancias_levenshtein)
        # Calcular precisión basada en coincidencia mínima de 4 caracteres
        accuracy_min4 = np.mean(coincidencias_min4)
        
        resultados.append({
            'implementacion': i+1,
            'accuracy_completa': accuracy_completa,
            'distancia_levenshtein_promedio': distancia_promedio,
            'accuracy_min4': accuracy_min4
        })
    return resultados

# Rutas a los archivos
#carpeta_txt = "../datasets/AOLP/AOLP/Subset_AC/Subset_AC/Subset_AC/groundtruth_recognition"
#carpeta_txt = "../datasets/AOLP/AOLP/Subset_LE/Subset_LE/Subset_LE/groundtruth_recognition"
carpeta_txt = "../datasets/AOLP/AOLP/Subset_RP/Subset_RP/Subset_RP/groundtruth_recognition"

#csv_file = './ocr_results_aolp_ac.csv'
#csv_file = './ocr_results_aolp_le.csv'
csv_file = './ocr_results_aolp_rp.csv'


# Leer los datos
respuestas_correctas = leer_respuestas_correctas(carpeta_txt)
predicciones = leer_predicciones(csv_file)

# Evaluar los modelos
resultados = evaluar_modelos(predicciones, respuestas_correctas)

# Mostrar resultados
for resultado in resultados:
    print(f"Implementación {resultado['implementacion']}:")
    print(f"  Accuracy Completa: {resultado['accuracy_completa']}")
    print(f"  Distancia Levenshtein Promedio: {resultado['distancia_levenshtein_promedio']}")
    print(f"  Accuracy con al menos 4 coincidencias: {resultado['accuracy_min4']}\n")
