
from math import atan2
from flask import Flask, jsonify, request
from numpy import cos, radians, sin, sqrt
from flask_cors import CORS
from elevation import get_elevation, get_tiff_bounds, merge_tiff_files
from atmospherical import attenuationByWaterVapor, GetAtmosphericGasesDataBetween63and350, GetAtmosphericGasesDataMinus57, GetAtmosphericGasesDataBetween57and63
import rasterio

# Ruta al archivo GeoTIFF de elevación descargado

app = Flask(__name__)

# Setteo la variable global de la data

global elevationDataPath
global elevationData
elevationDataPath = './elevation-profile-data/1.tif'

# Abre el archivo GeoTIFF y almacena los datos en una variable global
with rasterio.open(elevationDataPath) as src:
    elevationData = src.read(1)

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

# Definición de la función que calcula el perfil de elevación
def calculate_elevation_profile(start_point, end_point):
    # Cálculo de la distancia entre los dos puntos
    distance = calculate_distance(start_point, end_point)
    
    # Cálculo de la elevación para cada punto a lo largo de la línea entre los dos puntos
    elevations = []
    for i in range(1000):
        fraction = i / 1000.0
        lat = start_point['lat'] + fraction * (end_point['lat'] - start_point['lat'])
        lng = start_point['lng'] + fraction * (end_point['lng'] - start_point['lng'])
        elev = get_elevation(elevationData, src, lat, lng)
        elevations.append(int(elev))
    
    # Devolución de los datos como un arreglo JSON

    return {'elevations': elevations, 'linkDistance': distance}

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
    elevation_profile = calculate_elevation_profile(start_point, end_point)
    
    # Devolución de los datos como un arreglo JSON
    return jsonify(elevation_profile)
    # return jsonify({'elevations': [300, 400]})

# Definición de la función que calcula la distancia entre dos puntos de latitud y longitud
def calculate_distance(start_point, end_point):
    # Conversión de las coordenadas de latitud y longitud a radianes
    lat1 = radians(start_point['lat'])
    lng1 = radians(start_point['lng'])
    lat2 = radians(end_point['lat'])
    lng2 = radians(end_point['lng'])
    
    # Cálculo de la distancia utilizando la fórmula de Haversine
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlng / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    R = 6371 # Radio de la Tierra en kilómetros
    distance = R * c
    
    # Devolución de la distancia en kilómetros
    return distance

@app.route("/")
def main_():
        return "flask is running"