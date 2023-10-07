import rasterio
from rasterio.merge import merge
from numpy import cos, radians, sin, sqrt, linspace, degrees
from math import atan2

# Ruta al archivo GeoTIFF de elevación descargado
DEM_FILE_PATH = './elevation-profile-data/elevation-profile-Venezuela.tif'
global elevationData

def get_points_between(start_lat, start_lon, end_lat, end_lon, num_points):
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
                                elevationDataList):
    
    # Cálculo de la distancia entre los dos puntos
    distance = calculate_distance(start_point, end_point)

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

    tiff_image_of_point = [elevationDataList[0]]
    geographicDataSource = rasterio.open('./Venezuela-elevation-data' + tiff_image_of_point[0])
    elevationData = geographicDataSource.read(1)

    for lat, lon in points:

        # Busco que tiff file le corresponde al
        # Punto en el que estoy parado y lo comparo con el archivo
        # Tiff que tengo cargado en memoria

        print("Buscando el tiff file para lat ", lat)
        print("Buscando el tiff file para lon ", lon)
        tiff_file = find_tiff_file(lat, lon, elevationDataList)

        print("El tiff file que corresponde con el punto es: ", tiff_file[0])

        # Si el tiff file cambia, cargo el nuevo tiff file en memoria
        # Para buscar la elevacion en el punto que cae sobre el

        if tiff_image_of_point[0] != tiff_file[0]:

            geographicDataSource = rasterio.open('./Venezuela-elevation-data' + tiff_file[0])
            elevationData = geographicDataSource.read(1)
            tiff_image_of_point = tiff_file
        
        # Obtengo la elevacion en el archivo tiff que tengo en memoria

        elev = get_elevation(elevationData, geographicDataSource, lat, lon)
        elevations.append(int(elev))

    return {'elevations': elevations, 'linkDistance': distance}

    # for i in range
    
    # Cálculo de la elevación para cada punto a lo largo de la línea entre los dos puntos
    # elevations = []
    # for i in range(1000):
    #     fraction = i / 1000.0
    #     lat = start_point['lat'] + fraction * (end_point['lat'] - start_point['lat'])
    #     lng = start_point['lng'] + fraction * (end_point['lng'] - start_point['lng'])
    #     elev = get_elevation(elevationDataList, lat, lng)
    #     elevations.append(int(elev))
    
    # # Devolución de los datos como un arreglo JSON

    # return {'elevations': elevations, 'linkDistance': distance}

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
    x, y = geographicData.index(lng, lat)
    
    # Extracción de la elevación del archivo GeoTIFF en las coordenadas especificadas
    elev = elevationData[int(y)][int(x)]
    
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