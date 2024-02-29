
from flask import Flask, jsonify, request
from flask_cors import CORS
from elevation import calculate_azimuth, calculate_elevation_profile, get_surface_points, get_tiff_bounds, merge_tiff_files, get_parallel_points
from atmospherical import attenuationByWaterVapor, GetAtmosphericGasesDataBetween63and350, GetAtmosphericGasesDataMinus57, GetAtmosphericGasesDataBetween57and63
import rasterio
import json
import os
import numpy as np

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
    
    return archivos_json

venezuelaTiffData = get_tiff_data('./Venezuela-elevation-data')

CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# refrectividad_delta = radio_refractive_index(1015.7, , 69)

def calculateAtenuationInFrecuency(pressure, temperature, frecuency):

    atenuationValue = 0;

    if frecuency <= 57:

        atenuationValue = GetAtmosphericGasesDataMinus57(frecuency, pressure, temperature)

    if frecuency > 57 and frecuency < 63:

        atenuationValue = GetAtmosphericGasesDataBetween57and63(frecuency, pressure, temperature)

    if frecuency >= 63 and frecuency <= 350:
        atenuationValue = GetAtmosphericGasesDataBetween63and350(frecuency, pressure, temperature)

    return {'atenuationValue': atenuationValue}

def calculateWaterVaporAtenuation(pressure, temperature, waterDensity, frecuency):

    atenuationValue = attenuationByWaterVapor(frecuency, pressure, temperature, waterDensity)

    return {'atenuationValue': atenuationValue}

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

def get3dCoordinates(latitude1, longitude1, latitude2, longitude2, tiff_path):
    # Cargar la imagen TIFF
    dataset = rasterio.open(tiff_path)

    # Convertir latitud y longitude a coordenadas de píxeles
    row1, col1 = dataset.index(longitude1, latitude1)
    row2, col2 = dataset.index(longitude2, latitude2)

    # Leer los valores de los píxeles
    z = dataset.read(1)  # Lee los valores del primer canal (banda) de la imagen
    z_values = z[row1:row2+1, col1:col2+1]  # Extrae los valores de los píxeles en el área de interés

    # Crear una malla de coordenadas X e Y
    x = np.arange(col1, col2+1)  # Coordenadas X
    y = np.arange(row1, row2+1)  # Coordenadas Y
    xx, yy = np.meshgrid(x, y)  # Malla de coordenadas X e Y

    # Aplanar las matrices de coordenadas X, Y y valores de píxeles
    xx = xx.flatten()
    yy = yy.flatten()
    zz = z_values.flatten()

    # Crear el objeto con los arreglos de coordenadas
    coordenadas = {
        'x': xx.tolist(),
        'y': yy.tolist(),
        'z': zz.tolist()
    }

    print(coordenadas)

    return coordenadas

def obtener_coordenadas_punto(latitud, longitud, tiff_path):
    # Cargar la imagen TIFF
    dataset = rasterio.open(tiff_path)

    # Convertir latitud y longitud a coordenadas de píxeles
    row, col = dataset.index(longitud, latitud)

    # Leer el valor del píxel en el punto especificado
    z = dataset.read(1)  # Lee los valores del primer canal (banda) de la imagen
    z_value = z[row, col]

    # Obtener las coordenadas x e y correspondientes al punto
    x, y = dataset.xy(row, col)

    # Crear el objeto con las coordenadas
    coordenadas = {
        'x': x,
        'y': y,
        'z': z_value
    }

    print(coordenadas)

    return coordenadas

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
@app.route('/parallel_points', methods=['POST'])
def parallel_points():
    
    # Obtención de los datos de laty lng de los puntos de inicio y fin de la línea de perfil de elevación
    start_point = request.json['start_point']
    end_point = request.json['end_point']
    
    # Cálculo del perfil de elevación
    parallel_points = get_parallel_points(start_point['lat'], 
                                          start_point['lng'], 
                                          end_point['lat'], 
                                          end_point['lng'],
                                          2,
                                          -20)
    
    # Devolución de los datos como un arreglo JSON
    return jsonify(parallel_points)
    # return jsonify({'elevations': [300, 400]})

@app.route('/surface_points', methods=['POST'])
def surface_points():
    
    start_point = request.json['start_point']
    end_point = request.json['end_point']
    
    surface_points = get_surface_points(start_point['lat'], 
                                          start_point['lng'], 
                                          end_point['lat'], 
                                          end_point['lng'],
                                          venezuelaTiffData)
    
    # Devolución de los datos como un arreglo JSON
    return jsonify(surface_points)

@app.route('/elevation_profile', methods=['POST'])
def elevation_profile():
    
    # Obtención de los datos de laty lng de los puntos de inicio y fin de la línea de perfil de elevación
    start_point = request.json['start_point']
    end_point = request.json['end_point']
    antenna_1_height = request.json['antenna_1_height']
    antenna_2_height = request.json['antenna_2_height']
    
    # Cálculo del perfil de elevación
    elevation_profile = calculate_elevation_profile(start_point, 
                                                    end_point,
                                                    venezuelaTiffData,
                                                    antenna_1_height,
                                                    antenna_2_height)
    
    # Devolución de los datos como un arreglo JSON
    return jsonify(elevation_profile)
    # return jsonify({'elevations': [300, 400]})

@app.route('/get_specific_atmospheric_atenuation', methods=['POST'])
def getSpecificAtn():

    pressure = request.json['pressure']
    temperature = request.json['temperature']
    frecuency = request.json['frecuency']

    atmosAtn = calculateAtenuationInFrecuency(pressure, temperature, frecuency)
    return jsonify(atmosAtn)

@app.route('/get_specific_atmospheric_atenuation_water_vapor', methods=['POST'])
def getSpecificWaterAtn():

    pressure = request.json['pressure']
    temperature = request.json['temperature']
    waterDensity = request.json['waterDensity']
    frecuency = request.json['frecuency']

    atmosAtn = calculateWaterVaporAtenuation(pressure, temperature, waterDensity, frecuency)
    return jsonify(atmosAtn)

@app.route('/surface-coords', methods=['GET'])
def getSurfaceCoordinates():

    lat1 = request.json['lat1']
    lat2 = request.json['lat2']
    lng1 = request.json['lng1']
    lng2 = request.json['lng2']

@app.route('/get_azimuth', methods=['POST'])
def get_azimuth():
    
    # Obtención de los datos de laty lng de los puntos de inicio y fin de la línea de perfil de elevación
    start_point = request.json['start_point']
    start_height = request.json['start_height']
    end_point = request.json['end_point']
    end_height = request.json['end_height']

    azimuth = calculate_azimuth(start_point['lat'], 
                                start_point['lng'],
                                start_height, 
                                end_point['lat'], 
                                end_point['lng'],
                                end_height)

    return azimuth


@app.route("/")
def main_():
        return "flask is running"