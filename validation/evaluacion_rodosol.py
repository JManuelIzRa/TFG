import csv
import os
import re
import numpy as np
from sklearn.metrics import accuracy_score
from Levenshtein import distance as levenshtein_distance

def preprocesar_texto(texto):
    # Eliminar caracteres [ ], . , - y espacios
    # Eliminar caracteres especiales del abecedario, incluyendo acentos, diéresis, y otros caracteres diacríticos
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

def leer_respuesta_correcta_txt(archivo_txt):
    # Leer el archivo .txt y extraer la línea con la matrícula (plate)
    with open(archivo_txt, 'r') as f:
        for linea in f:
            if linea.startswith("plate:"):
                # Extraer la matrícula y preprocesarla
                matricula = linea.split("plate:")[1].strip()
                return preprocesar_texto(matricula)
    return None

def leer_respuestas_correctas(carpeta_txt):
    respuestas_correctas = {}

    indice_minimo = 4001
    indice_maximo = 5000
    contador =  0

    for archivo in os.listdir(carpeta_txt):
        if archivo.endswith('.txt'):
            if contador >= indice_minimo and contador <= indice_maximo:
                archivo_path = os.path.join(carpeta_txt, archivo)
                respuestas_correctas[archivo] = leer_respuesta_correcta_txt(archivo_path)
            contador += 1
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
carpeta_txt = "../datasets/tbFcZE-RodoSol-ALPR/RodoSol-ALPR/images/cars-br"  # Cambia esta ruta a tu carpeta de archivos .txt
csv_file = './ocr_results_rodosol_5_5.csv'  # Cambia esta ruta al archivo CSV de predicciones

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
