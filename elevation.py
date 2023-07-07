import rasterio
from rasterio.merge import merge

# Ruta al archivo GeoTIFF de elevación descargado
DEM_FILE_PATH = './elevation-profile-data/elevation-profile-Venezuela.tif'

# Definición de la función que obtiene la elevación de un punto de latitud y longitud
def get_elevation(elevationData, src, lat, lng):

    # Transformación de las coordenadas de latitud y longitud a coordenadas de la proyección del archivo GeoTIFF
    x, y = src.index(lng, lat)
    
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