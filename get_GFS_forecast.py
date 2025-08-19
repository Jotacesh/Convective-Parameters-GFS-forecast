# Script descarga variables necesarias para el cálculo de parámetros convectivos del producto GFS. Acota una región específica y descarga solo las variables que son necesarias.
# Las variables contienen perfiles verticales de: presión, altura geopotencial, temperatura, temperatura del punto de rocío, velocidad zonal y meridional. 
# autor: Javier Campos
# date: 10-08-2025

#%%
import os
import requests

# Autor: Javier Campos NÃºÃ±ez 
# Fecha: 17-06-2025
# DescripciÃ³n: Descarga pronósticos de GFS con las variables necesarias para calcular
# parámetros convectivos.

# Definir región
lat_n = -30
lat_s = -55
lon_o = -85
lon_e = -67

# ----- Sección para permitir ingreso de variable fuera del codigo -----
# example: python promedios_mensuales.py --var SRH_500m_LM
import argparse
parser = argparse.ArgumentParser(description='Define la fecha de inicializacion del pronostico gfs')
parser.add_argument('--var', type=str, default="20250729", help='Fecha en formato yyyymmdd')
args = parser.parse_args()

# Usar la variable
var = args.var
print(f'Fecha de inicializacion: {var}')


# Definir fecha y parámetros
date = var  # formato yyyymmdd
init = "00"
res = "0p25"
fhour=f"{0:03d}"
# URL base
base_url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_{res}.pl?dir=%2Fgfs.{date}%2F{init}%2Fatmos&file=gfs.t{init}z.pgrb2.{res}.f{fhour}"
params_fixed = (
    f"&var_HGT=on&var_MSLET=on&var_PRMSL=on&var_RH=on&var_SPFH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&var_PRES=on&var_DPT=on"
    f"&lev_1000_mb=on&lev_975_mb=on&lev_950_mb=on&lev_925_mb=on&lev_900_mb=on&lev_850_mb=on"
    f"&lev_800_mb=on&lev_750_mb=on&lev_700_mb=on&lev_650_mb=on&lev_600_mb=on&lev_550_mb=on"
    f"&lev_500_mb=on&lev_450_mb=on&lev_400_mb=on&lev_350_mb=on&lev_300_mb=on&lev_250_mb=on"
    f"&lev_200_mb=on&lev_150_mb=on&lev_100_mb=on&lev_surface=on&lev_mean_sea_level=on"
    f"&lev_2_m_above_ground=on&lev_10_m_above_ground=on"
)
subregion = f"&subregion=&toplat={lat_n}&leftlon={lon_o}&rightlon={lon_e}&bottomlat={lat_s}"

# Crear carpeta destino
destino= f"descargas_gfs/{date}_t{init}"
os.makedirs(destino, exist_ok=True)

#%% Iterar sobre las horas de pronóstico con barra de progreso
import requests
from tqdm import tqdm
import os
# Definir paso y horas máximas
step = 3  # paso entre horas de pronóstico
max_hour = 120
# Iterar sobre las horas de pronóstico
for i in range(0, max_hour + 1, step):
    fhour = f"{i:03d}"
    file_param = f"&file=gfs.t{init}z.pgrb2.{res}.f{fhour}"
    url = base_url + file_param + params_fixed + subregion
    nombre_archivo = f"{destino}/gfs{res}_t{init}z_{date}_f{fhour}.grb2"

    # Saltar si ya existe   ------------- sección realizada por chatGPT :D
    if os.path.exists(nombre_archivo):
        print(f"{nombre_archivo} ya existe, saltando...")
        continue

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))

        with open(nombre_archivo, "wb") as f, tqdm(
            desc=f"Descargando f{fhour}",
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            ncols=80
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))

    except Exception as e:
        print(f"Error al descargar f{fhour}: {e}")
			# ---------------------------------------------

# Une GFS en un solo archivo netCDF
# GFS grib files tienen TypeOfLevel, entre esos los niveles de presión, de superficie, sobre el nivel del suelo (2 y 10m para las variables descargadas) y nivel medio del mar.
import xarray as xr
import glob
#%%
archivos= glob.glob(f"{destino}/gfs{res}_t{init}z_{date}_f*.grb2") # selecciona todos los archivos de GFS descargados
df = [xr.open_dataset(archivo, engine='cfgrib',backend_kwargs={"filter_by_keys": {"typeOfLevel": "isobaricInhPa"}}) for archivo in archivos]
dx1 = [xr.open_dataset(archivo, engine='cfgrib',backend_kwargs={"filter_by_keys": {"typeOfLevel": "surface"}}) for archivo in archivos]
dx2 = [xr.open_dataset(archivo, engine='cfgrib',backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround", "level": 2}}) for archivo in archivos]
dx3 = [xr.open_dataset(archivo, engine='cfgrib',backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround", "level": 10}}) for archivo in archivos]
dx4 = [xr.open_dataset(archivo, engine='cfgrib',backend_kwargs={"filter_by_keys": {"typeOfLevel": "meanSea"}}) for archivo in archivos]

#%% concatenar a lo largo del tiempo

ds= xr.concat(df, dim='valid_time')
ds1=xr.concat(dx1,dim='valid_time') # variables
ds2=xr.concat(dx2,dim='valid_time') # de 
ds3=xr.concat(dx3,dim='valid_time') # superficie
ds4=xr.concat(dx4,dim='valid_time')

# deja todas las variables de superficie (2, 10m, surface y meansealevel) en un solo dataset.
ds1['t2m']=ds2.t2m
ds1['r2']=ds2.r2
ds1['d2m']=ds2.d2m
ds1['u10']=ds3.u10
ds1['v10']=ds3.v10
ds1['mslp']=ds4.prmsl

# elimina variables redundantes
ds = ds.drop_vars(['time', 'step'])
ds1 = ds1.drop_vars(['time', 'step'])
#%% ordena los datasets en la dimensión del tiempo
ds=ds.sortby('valid_time')
ds1=ds1.sortby('valid_time')

# crea los archivos netcdf
ds.to_netcdf(f"{destino}/gfs{res}_t{init}z_{date}_pl.nc")
ds1.to_netcdf(f"{destino}/gfs{res}_t{init}z_{date}_surface.nc")
print('se gener\'o el archivo netcdf')
[os.remove(f) for f in glob.glob(f"{destino}/gfs{res}_t{init}z_{date}_f*.grb2")]
[os.remove(f) for f in glob.glob(f"{destino}/gfs{res}_t{init}z_{date}_f*.idx")]

print('se eliminaron archivos temporales')

