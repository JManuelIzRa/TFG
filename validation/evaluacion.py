import csv
import json
import os
import re
import numpy as np
from sklearn.metrics import accuracy_score
from Levenshtein import distance as levenshtein_distance

def preprocesar_texto(texto):
    # Eliminar caracteres [ ], . , - y espacios
    texto = re.sub(r'[ªº\\!|\"@·#$%&/()=:;?¿\'¡`^[\]+*´{}_\-.,<>~€¬]', '', texto)
    texto = re.sub(r'[àáâäæãåā]', 'a', texto)
    texto = re.sub(r'[èéêëēėę]', 'e', texto)
    texto = re.sub(r'[ìíîïīįì]', 'i', texto)
    texto = re.sub(r'[òóôöøōõ]', 'o', texto)
    texto = re.sub(r'[ùúûüū]', 'u', texto)
    texto = re.sub(r'[ç]', 'c', texto)
    texto = re.sub(r'[ñ]', 'n', texto)
    texto = re.sub(r'[ÿý]', 'y', texto)
    
    # Quitar espacios
    texto = texto.replace(' ', '')   
    texto = texto.upper()
    return texto

def leer_respuestas_correctas(carpeta_json):
    respuestas_correctas = {}
    for archivo in os.listdir(carpeta_json):
        if archivo.endswith('.json'):
            with open(os.path.join(carpeta_json, archivo), 'r') as f:
                datos = json.load(f)
                matricula = datos['license_plate'].upper()
                respuestas_correctas[archivo] = preprocesar_texto(matricula)
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
    archivos_json = list(respuestas_correctas.keys())

    for i, implementacion in enumerate(predicciones):
        y_true = []
        y_pred = []
        distancias_levenshtein = []
        coincidencias_min4 = []

        for j, prediccion in enumerate(implementacion):
            archivo_json = archivos_json[j]
            respuesta_correcta = respuestas_correctas[archivo_json]
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
#carpeta_json = "../datasets/validation_labeled"
carpeta_json = "..\\datasets\\baza_slika\\040603"
#csv_file = './ocr_results_self_made2.csv'
csv_file = './ocr_results_baza_slika_rep.csv'

# Leer los datos
respuestas_correctas = leer_respuestas_correctas(carpeta_json)
predicciones = leer_predicciones(csv_file)

# Evaluar los modelos
resultados = evaluar_modelos(predicciones, respuestas_correctas)

# Mostrar resultados
for resultado in resultados:
    print(f"Implementación {resultado['implementacion']}:")
    print(f"  Accuracy Completa: {resultado['accuracy_completa']}")
    print(f"  Distancia Levenshtein Promedio: {resultado['distancia_levenshtein_promedio']}")
    print(f"  Accuracy con al menos 4 coincidencias: {resultado['accuracy_min4']}\n")

