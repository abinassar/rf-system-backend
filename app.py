
from flask import Flask, jsonify, request
from flask_cors import CORS
from elevation import get_points_between, find_tiff_files, calculate_elevation_profile, get_tiff_bounds, merge_tiff_files
from atmospherical import attenuationByWaterVapor, GetAtmosphericGasesDataBetween63and350, GetAtmosphericGasesDataMinus57, GetAtmosphericGasesDataBetween57and63
import rasterio
import json
import os

# Ruta al archivo GeoTIFF de elevación descargado

app = Flask(__name__)

# Setteo la variable global de la data

global elevationDataPath
global elevationData
global venezuelaTiffData
elevationDataPath = './elevation-profile-data/1.tif'

def get_tiff_data(carpeta):
    # Lista para almacenar los objetos JSON
    archivos_json = []

    # Obtener la lista de archivos en la carpeta
    archivos_tiff = [archivo for archivo in os.listdir(carpeta) if archivo.endswith('.tif')]

    # Iterar sobre los archivos TIFF
    for archivo in archivos_tiff:
        # Ruta completa al archivo TIFF
        archivo_tiff = os.path.join(carpeta, archivo)

        # Obtener los límites geográficos del archivo TIFF
        with rasterio.open(archivo_tiff) as src:
            bounds = get_tiff_bounds(src)
            lon_min, lat_min, lon_max, lat_max = bounds

        # Crear el objeto JSON
        info = {
            'nombre_archivo': archivo,
            'latitud_minima': lat_min,
            'latitud_maxima': lat_max,
            'longitud_minima': lon_min,
            'longitud_maxima': lon_max
        }

        # Agregar el objeto JSON a la lista
        archivos_json.append(info)
    
    # Convertir la lista de objetos JSON a una cadena JSON
    archivos_json_str = json.dumps(archivos_json, indent=4)

    # # Guardar la cadena JSON en un archivo
    # with open('info_tiff.json', 'w') as archivo_json:
    #     archivo_json.write(archivos_json_str)

    # # Imprimir la cadena JSON en la consola
    # print(archivos_json_str)
    return archivos_json


# Abre el archivo GeoTIFF y almacena los datos en una variable global
# with rasterio.open(elevationDataPath) as src:
#     elevationData = src.read(1)
#     bounds = get_tiff_bounds(src)

# # bounds es una tupla en el formato (lon_min, lat_min, lon_max, lat_max)
# lon_min, lat_min, lon_max, lat_max = bounds

# # Imprime los límites geográficos
# print("Límites geográficos:")
# print("Latitud mínima:", lat_min)
# print("Latitud máxima:", lat_max)
# print("Longitud mínima:", lon_min)
# print("Longitud máxima:", lon_max)

venezuelaTiffData = get_tiff_data('./Venezuela-elevation-data')

#CONSEGUIR TIFF FILES PARA DOS PUNTOS DE LATITUD Y LONGITUD

# testfiles = find_tiff_files(3.5804,-64.5604, 2.3937,-63.4201, venezuelaTiffData)

# tiff_json = json.dumps(testfiles, indent=4)
# print(tiff_json)

# TESTEAR PUNTOS ENTRE DOS LATITUDES Y LONGITUDES

# start_lat = 40.7128  # Latitud del punto de partida (Nueva York)
# start_lon = -74.0060  # Longitud del punto de partida (Nueva York)
# end_lat = 34.0522  # Latitud del punto de destino (Los Ángeles)
# end_lon = -118.2437  # Longitud del punto de destino (Los Ángeles)
# num_points = 1000  # Número de puntos intermedios

# points = get_points_between(start_lat, start_lon, end_lat, end_lon, num_points)

# # Imprimir los puntos intermedios
# for lat, lon in points:
#     print("lat ", lat)
#     print("lon ", lon)

CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})

def calculateAtmosphericAtenuation(pressure, temperature):

    atenuationsPoints = []

    for superiorIndex in range(0, 350):

        # I set the ten values for each Ghz

        # for inferiorIndex in range(0, 9):

        frecuency = float(str(superiorIndex));
        atenuationValue = 0;

        print("superiorIndex: ", superiorIndex) 
        print("frecuency: ", frecuency)   
        print("numero que falla ", GetAtmosphericGasesDataMinus57(frecuency, pressure, temperature)) 

        if superiorIndex <= 57:

            atenuationValue = GetAtmosphericGasesDataMinus57(frecuency, pressure, temperature)

            atenuationPoint = {'atenuation': atenuationValue,
                               'frecuency': frecuency}

            atenuationsPoints.append(atenuationPoint)

        if superiorIndex > 57 and superiorIndex < 63:

            atenuationValue = GetAtmosphericGasesDataBetween57and63(frecuency, pressure, temperature)
            atenuationPoint = {'atenuation': atenuationValue,
                               'frecuency': frecuency}
            
            atenuationsPoints.append(atenuationPoint)

        if superiorIndex >= 63 and superiorIndex <= 350:
            atenuationValue = GetAtmosphericGasesDataBetween63and350(frecuency, pressure, temperature)

            atenuationPoint = {'atenuation': atenuationValue,
                               'frecuency': frecuency}

            atenuationsPoints.append(atenuationPoint)
    
    return {'atenuationsPoints': atenuationsPoints}

@app.route('/get_atmospheric_atenuation_water_vapor', methods=['POST'])
def getWaterVaporAtenuation():
    
    pressure = request.json['pressure']
    temperature = request.json['temperature']
    waterDensity = request.json['waterDensity']
    atenuationsPoints = []

    for superiorIndex in range(0, 350):

        # I set the ten values for each Ghz

        # for inferiorIndex in range(0, 9):

        frecuency = float(str(superiorIndex));
        atenuationValue = 0;

        atenuationValue = attenuationByWaterVapor(frecuency, pressure, temperature, waterDensity)

        atenuationPoint = {'atenuation': atenuationValue,
                           'frecuency': frecuency}

        atenuationsPoints.append(atenuationPoint)
    
    return {'atenuationsPoints': atenuationsPoints}

@app.route('/get_atmospheric_atenuation', methods=['POST'])
def getAtmosphericAtn():

    pressure = request.json['pressure']
    temperature = request.json['temperature']

    atmosAtn = calculateAtmosphericAtenuation(pressure, temperature)
    return jsonify(atmosAtn)

@app.route('/tiff_bounds', methods=['GET'])
def tiff_bounds():
    min_lon, min_lat, max_lon, max_lat = get_tiff_bounds(src)
    return jsonify({
        'min_lon': min_lon,
        'min_lat': min_lat,
        'max_lon': max_lon,
        'max_lat': max_lat
    })

@app.route('/merge-tiff', methods=['POST'])
def merge_tiff_files2():

    tiff_files = ['merged.tif', 'tif-unido-1.tif']
    output_file = 'tif-elevaciones-Venezuela.tif'
    merge_tiff_files(tiff_files, output_file)
    return jsonify({
        'status': "Ok"
    })

# Definición de la ruta de la API
@app.route('/elevation_profile', methods=['POST'])
def elevation_profile():

    # Obtención de los datos de laty lng de los puntos de inicio y fin de la línea de perfil de elevación
    start_point = request.json['start_point']
    end_point = request.json['end_point']
    
    # Cálculo del perfil de elevación
    elevation_profile = calculate_elevation_profile(start_point, 
                                                    end_point,
                                                    venezuelaTiffData)
    
    # Devolución de los datos como un arreglo JSON
    return jsonify(elevation_profile)
    # return jsonify({'elevations': [300, 400]})

@app.route("/")
def main_():
        return "flask is running"