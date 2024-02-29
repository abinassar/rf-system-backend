import rasterio
import math
import numpy
from rasterio.merge import merge
from numpy import cos, radians, sin, sqrt, linspace, degrees
from math import atan2
from AltAzRange import AltAzimuthRange

# Ruta al archivo GeoTIFF de elevación descargado
DEM_FILE_PATH = './elevation-profile-data/elevation-profile-Venezuela.tif'
global elevationData

def get_points_between(start_lat, 
                       start_lon, 
                       end_lat, 
                       end_lon, 
                       num_points):
    
    # Convertir los puntos de latitud y longitud a radianes
    start_lat_rad = radians(start_lat)
    start_lon_rad = radians(start_lon)
    end_lat_rad = radians(end_lat)
    end_lon_rad = radians(end_lon)

    # Calcular la distancia en radianes entre los puntos
    d_lat = end_lat_rad - start_lat_rad
    d_lon = end_lon_rad - start_lon_rad

    # Calcular los incrementos en latitud y longitud
    lat_increments = linspace(0, d_lat, num_points)
    lon_increments = linspace(0, d_lon, num_points)

    # Calcular los puntos intermedios
    intermediate_points = []
    for i in range(num_points):
        lat = start_lat_rad + lat_increments[i]
        lon = start_lon_rad + lon_increments[i]
        intermediate_points.append((degrees(lat), degrees(lon)))

    return intermediate_points

# Definición de la función que calcula el perfil de elevación
def calculate_elevation_profile(start_point, 
                                end_point,
                                elevationDataList,
                                height_antenna_1,
                                height_antenna_2):
    
    azimuth_antenna_1 = calculate_azimuth(start_point['lat'], 
                                        start_point['lng'],
                                        height_antenna_1, 
                                        end_point['lat'], 
                                        end_point['lng'],
                                        height_antenna_2)

    azimuth_antenna_2 = calculate_azimuth(end_point['lat'], 
                                        end_point['lng'],
                                        height_antenna_2,
                                        start_point['lat'], 
                                        start_point['lng'],
                                        height_antenna_1)

    # Cálculo de la distancia entre los dos puntos
    # distance = calculate_distance(start_point, end_point)
    distance = calcular_distancia_linea_recta(start_point['lat'], 
                                              start_point['lng'], 
                                              100,
                                              end_point['lat'],
                                              end_point['lng'],
                                              100)

    # Calc distance between the point a and b 
    # Around the sphere

    # curve_distance = haversine([start_point['lng'], 
    #                             start_point['lat']], 
    #                             [end_point['lng'], 
    #                             end_point['lat']])

    curve_distance = calcular_distancia(start_point['lat'], 
                                        start_point['lng'], 
                                        end_point['lat'],
                                        end_point['lng'])

    distance_reflection = calculateReflectionPoint(curve_distance,
                                                   1.33,
                                                   100,
                                                   100)

    # Obtengo todos los 1000 puntos de latitudes y longitudes entre los dos puntos

    num_points = 1000

    points = get_points_between(start_point['lat'], 
                                start_point['lng'], 
                                end_point['lat'], 
                                end_point['lng'], 
                                num_points)
    elevations = []
    
    # Calculo las elevaciones de cada punto
    # Cargando la imagen tiff respectiva a ese punto geografico

    tiff_image_of_point = [""]

    for lat, lon in points:

        # Busco que tiff file le corresponde al
        # Punto en el que estoy parado y lo comparo con el archivo
        # Tiff que tengo cargado en memoria

        # print("Buscando el tiff file para lat ", lat)
        # print("Buscando el tiff file para lon ", lon)

        tiff_file = find_tiff_file(lat, lon, elevationDataList)

        # print("El tiff file que corresponde con el punto es: ", tiff_file[0])

        # Si el tiff file cambia, cargo el nuevo tiff file en memoria
        # Para buscar la elevacion en el punto que cae sobre el

        if tiff_image_of_point[0] != tiff_file[0]:


            geographicDataSource = rasterio.open('./Venezuela-elevation-data/' + tiff_file[0])
            elevationData = geographicDataSource.read(1)
            tiff_image_of_point = tiff_file
            print("El documento tiff es: " + tiff_image_of_point[0])
        
        # Obtengo la elevacion en el archivo tiff que tengo en memoria

        # TODO: En este caso dem es geographicDataSource

        elev = get_elevation(elevationData, lat, lon, geographicDataSource)
        elevations.append(int(elev))

    return {'elevations': elevations, 
            'linkDistance': distance,
            'curveDistance': curve_distance,
            'reflectionDistance': distance_reflection,
            'azimuthAntenna1': azimuth_antenna_1,
            'azimuthAntenna2': azimuth_antenna_2}

def get_surface_points(lat1,
                       lng1,
                       lat2,
                       lng2,
                       venezuelaTiffData):

    surfacePointsList = []

    # Obtengo los n coordenadas paralelas a las principales que me da el usuario

    for i in range(-20, 20):

        # Declaro la distance en km como el indice entre 100
        # Por ejemplo: 20 / 100 = 0.2 km
        distance = i/100

        parallel_points = get_parallel_points(lat1, 
                                              lng1, 
                                              lat2, 
                                              lng2,
                                              2,
                                              distance)
        
        # Obtuve las coordenadas de los puntos paralelos a la linea principal

        start_point = {
            'lat': parallel_points[0][0],
            'lng': parallel_points[0][1]
        }

        end_point = {
            'lat': parallel_points[1][0],
            'lng': parallel_points[1][1]
        }

        # Con ello obtengo los puntos de superficie

        surfacePoints = calculate_elevation_surface_points(start_point,
                                                           end_point,
                                                           venezuelaTiffData,
                                                           distance)
        
        surfacePointsObject = {
            'surfacePoints': surfacePoints,
            'startPoint': start_point,
            'endPoint': end_point
        }

        surfacePointsList.append(surfacePointsObject)
    
    return {'surfaceCoordinates': surfacePointsList}

def calculate_elevation_surface_points(start_point, 
                                       end_point,
                                       elevationDataList,
                                       xCoordinate):
    
    # Cálculo de la distancia entre los dos puntos
    distance = calculate_distance(start_point, end_point)

    # Obtengo todos los 1000 puntos de latitudes y longitudes entre los dos puntos

    num_points = 1000
    start_yCoord = 0
    distance_fragment = distance / num_points

    points = get_points_between(start_point['lat'], 
                                start_point['lng'], 
                                end_point['lat'], 
                                end_point['lng'], 
                                num_points)
    coordinates = []
    
    # Calculo las elevaciones de cada punto
    # Cargando la imagen tiff respectiva a ese punto geografico

    tiff_image_of_point = [""]
    last_elev = 100

    for lat, lon in points:

        # Busco que tiff file le corresponde al
        # Punto en el que estoy parado y lo comparo con el archivo
        # Tiff que tengo cargado en memoria

        # print("Buscando el tiff file para lat ", lat)
        # print("Buscando el tiff file para lon ", lon)

        tiff_file = find_tiff_file(lat, lon, elevationDataList)

        # print("El tiff file que corresponde con el punto es: ", tiff_file[0])

        # Si el tiff file cambia, cargo el nuevo tiff file en memoria
        # Para buscar la elevacion en el punto que cae sobre el

        if tiff_image_of_point[0] != tiff_file[0]:

            geographicDataSource = rasterio.open('./Venezuela-elevation-data/' + tiff_file[0])
            elevationData = geographicDataSource.read(1)
            tiff_image_of_point = tiff_file
            print("El documento tiff es: " + tiff_image_of_point[0])
        
        # Obtengo la elevacion en el archivo tiff que tengo en memoria

        # TODO: En este caso dem es geographicDataSource

        elev = get_elevation(elevationData, lat, lon, geographicDataSource)

        if elev == -32767:
            elev = last_elev

        last_elev = elev

        surfaceCoordinate = {
            'x': xCoordinate,
            'y': start_yCoord,
            'z': int(elev)
        }
        coordinates.append(surfaceCoordinate)
        start_yCoord += distance_fragment

    return {'coordinates': coordinates, 'linkDistance': distance}

def get_parallel_points(start_lat, start_lon, end_lat, end_lon, num_points, distance):
    # Convertir los puntos de latitud y longitud a radianes
    start_lat_rad = math.radians(start_lat)
    start_lon_rad = math.radians(start_lon)
    end_lat_rad = math.radians(end_lat)
    end_lon_rad = math.radians(end_lon)

    # Calcular la distancia en radianes entre los puntos
    d_lat = end_lat_rad - start_lat_rad
    d_lon = end_lon_rad - start_lon_rad

    # Calcular los incrementos en latitud y longitud
    lat_increments = numpy.linspace(0, d_lat, num_points)
    lon_increments = numpy.linspace(0, d_lon, num_points)

    # Calcular los puntos intermedios en la línea principal
    intermediate_points = []
    for i in range(num_points):
        lat = start_lat_rad + lat_increments[i]
        lon = start_lon_rad + lon_increments[i]
        intermediate_points.append((math.degrees(lat), math.degrees(lon)))

    # Calcular el vector dirección de la línea principal
    direction_vector = (end_lat_rad - start_lat_rad, end_lon_rad - start_lon_rad)
    direction_vector_norm = math.hypot(direction_vector[0], direction_vector[1])
    direction_vector = (direction_vector[0] / direction_vector_norm, direction_vector[1] / direction_vector_norm)

    # Calcular el vector perpendicular a la línea principal
    perpendicular_vector = (direction_vector[1], -direction_vector[0])

    # Calcular los puntos paralelos a una distancia "d"
    parallel_points = []
    for point in intermediate_points:
        lat, lon = point
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        # Calcular el desplazamiento en latitud y longitud
        delta_lat = perpendicular_vector[0] * distance / 6371  # Aproximación de la Tierra como una esfera de radio 6371 km
        delta_lon = perpendicular_vector[1] * distance / (6371 * math.cos(lat_rad))

        # Calcular la nueva latitud y longitud
        new_lat = math.degrees(lat_rad + delta_lat)
        new_lon = math.degrees(lon_rad + delta_lon)

        parallel_points.append((new_lat, new_lon))

    return parallel_points

def find_tiff_files(lat1, lon1, lat2, lon2, tiff_files_list):
    tiff_files_list = []
    
    for archivo in tiff_files_list:
        nombre_archivo = archivo["nombre_archivo"]
        min_lat = archivo["latitud_minima"]
        max_lat = archivo["latitud_maxima"]
        min_lon = archivo["longitud_minima"]
        max_lon = archivo["longitud_maxima"]
        
        if (min_lat <= lat1 <= max_lat and min_lon <= lon1 <= max_lon) or \
           (min_lat <= lat2 <= max_lat and min_lon <= lon2 <= max_lon):
            tiff_files_list.append(nombre_archivo)
    
    return tiff_files_list

def find_tiff_file(lat1, lon1, tiff_files_list):
    tiff_file_list = []
    
    for archivo in tiff_files_list:
        nombre_archivo = archivo["nombre_archivo"]
        min_lat = archivo["latitud_minima"]
        max_lat = archivo["latitud_maxima"]
        min_lon = archivo["longitud_minima"]
        max_lon = archivo["longitud_maxima"]
        
        if (min_lat <= lat1 <= max_lat and min_lon <= lon1 <= max_lon):
            tiff_file_list.append(nombre_archivo)
    
    return tiff_file_list

# Definición de la función que obtiene la elevación de un punto de latitud y longitud
def get_elevation(elevationData, 
                  lat, 
                  lng,
                  geographicData):
    

    # Transformación de las coordenadas de latitud y longitud a coordenadas de la proyección del archivo GeoTIFF
    # x, y = geographicData.index(lng, lat)
    # x, y = rasterio.transform.rowcol(geographicData.transform, lng, lat)
    
    # Extracción de la elevación del archivo GeoTIFF en las coordenadas especificadas
    # elev = elevationData[int(y)][int(x)]

    # Esta modificacion genera puntos mas reales

    x, y = geographicData.index(lng, lat)
    elev = elevationData[x, y]
    
    return elev
    
def get_tiff_bounds(src):
    bounds = src.bounds
    min_lon, min_lat, max_lon, max_lat = bounds.left, bounds.bottom, bounds.right, bounds.top
    return min_lon, min_lat, max_lon, max_lat

def merge_tiff_files(tiff_files, output_file):
    # Abrir todos los archivos TIFF y leer sus datos
    src_files_to_mosaic = []
    for file in tiff_files:
        src = rasterio.open(file)
        src_files_to_mosaic.append(src)

    # Unir los archivos TIFF utilizando la función merge()
    mosaic, out_trans = merge(src_files_to_mosaic)

    # Crear un archivo TIFF de salida con los datos combinados
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": mosaic.shape[1],
                     "width": mosaic.shape[2],
                     "transform": out_trans})
    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(mosaic)

# Definición de la función que calcula la distancia entre dos puntos de latitud y longitud en linea recta
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

# Haversine function to get distance around the sphere

def haversine(coord1: object, coord2: object):
    import math

    # Coordinates in decimal degrees (e.g. 2.89078, 12.79797)
    lon1, lat1 = coord1
    lon2, lat2 = coord2

    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    meters = R * c  # output distance in meters
    km = meters / 1000.0  # output distance in kilometers

    meters = round(meters, 3)
    km = round(km, 3)
    return km

def calcular_distancia(latitud_a, longitud_a, latitud_b, longitud_b):
    radio_tierra = 6371  # Radio promedio de la Tierra en kilómetros

    # Convertir las coordenadas de grados a radianes
    latitud_a_rad = math.radians(latitud_a)
    longitud_a_rad = math.radians(longitud_a)
    latitud_b_rad = math.radians(latitud_b)
    longitud_b_rad = math.radians(longitud_b)

    # Diferencia de longitudes y latitudes
    dif_latitudes = latitud_b_rad - latitud_a_rad
    dif_longitudes = longitud_b_rad - longitud_a_rad

    # Fórmula de Haversine
    a = math.sin(dif_latitudes/2)**2 + math.cos(latitud_a_rad) * math.cos(latitud_b_rad) * math.sin(dif_longitudes/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distancia = radio_tierra * c

    return distancia

# Las alturas estan expresadas en meters
def calcular_distancia_linea_recta(latitud_a, longitud_a, altura_a, latitud_b, longitud_b, altura_b):
    radio_tierra = 6371  # Radio promedio de la Tierra en kilómetros

    # Convertir las coordenadas de grados a radianes
    latitud_a_rad = math.radians(latitud_a)
    longitud_a_rad = math.radians(longitud_a)
    latitud_b_rad = math.radians(latitud_b)
    longitud_b_rad = math.radians(longitud_b)

    # Convertir la altura de metros a kilómetros
    altura_a_km = altura_a / 1000
    altura_b_km = altura_b / 1000

    # Distancia horizontal en el plano terrestre
    distancia_horizontal = radio_tierra * math.acos(
        math.sin(latitud_a_rad) * math.sin(latitud_b_rad) +
        math.cos(latitud_a_rad) * math.cos(latitud_b_rad) *
        math.cos(longitud_b_rad - longitud_a_rad)
    )

    # Distancia en línea recta considerando la diferencia de alturas
    distancia_linea_recta = math.sqrt(distancia_horizontal**2 + (altura_b_km - altura_a_km)**2)

    return distancia_linea_recta

def calculateReflectionPoint(distance,
                           k_factor,
                           antenna1_height,
                           antenna2_height):
    
    earth_effective_radio = k_factor * 6371

    m = (pow(distance, 2)) / (4 * earth_effective_radio * (antenna1_height + antenna2_height))
    
    c = 0

    if antenna1_height > antenna2_height:
        c = (antenna1_height - antenna2_height) / (antenna1_height + antenna2_height)
    else:
        c = (antenna2_height - antenna1_height) / (antenna1_height + antenna2_height)

    b = 2 * math.sqrt((m + 1) / 3 * m) * math.cos(((math.pi/3) + (math.acos(((3 * c) / 2) * math.sqrt((3 * m) / pow(m + 1, 3))))))

    d1 = (distance * (1 + b)) / 2

    return d1

def calculate_azimuth(obsLat,
                     obsLng,
                     obsHeight,
                     targetLat,
                     targetLng,
                     targetHeight):
    
    satellite = AltAzimuthRange()
    satellite.observer(obsLat, obsLng, obsHeight)
    satellite.target(targetLat, targetLng, targetHeight)
    
    data = satellite.calculate()
    return data
