# Script utiliza archivos netcdf de superficie y de niveles verticales de GFS, generados por el script "git_GFS_forecast.py" para realizar el c�lculo de par�metros convectivos
# autor: Javier Campos
# fecha: 10-08-2025

#%%importar librer��as
import pandas as pd
import numpy as np
import xarray as xr
# ----- Seccion para permitir ingreso de variable fuera del codigo -----
# example: python promedios_mensuales.py --var SRH_500m_LM
import argparse
parser = argparse.ArgumentParser(description='Define la fecha de inicializacion del pronostico gfs')
parser.add_argument('--var', type=str, default="20250729", help='Fecha en formato yyyymmdd')
args = parser.parse_args()

# Usar la variable
var = args.var
print(f'Fecha de inicializacion: {var}')

fecha=var # formato yyyymmdd

#%% carga archivo de datos con xarray
ds=xr.open_dataset(rf'descargas_gfs/{fecha}_t00/gfs0p25_t00z_{fecha}_pl.nc',engine='netcdf4')

#%% se adecúa el código para que se pueda leer en thundeR, librería de R para calcular
# parámetros convectivos a partir de un perfil vertical
HR=ds.r.data
#%%
ind=HR<1
HR[ind]=1 # se eliminan valores negativos
HR=HR/100 # se pasa de % a fracción
#%%
w_speed=(ds.u.values**2+ds.v.values**2)**0.5
w_dir=np.mod(180+(180/np.pi) * np.arctan2(ds.u.values,ds.v.values) ,360) # https://confluence.ecmwf.int/pages/viewpage.action?pageId=133262398
#%% -------------------- Cálculo de temperatura de rocío (método anterior) -------------------------------
T=ds.t.values-273.15 # pasa K a °C
#%% carga altura geopotencial (en m2/s2)
H=ds.gh.values # se divide en g0=9.81 m/s2, para pasar a metros sobre el nivel del mar
#%% Thunder necesita Altura geopotencial [m], Temperatura [°C], Temperatura de rocío [°C], w_speed [m/s], w_dir [°]
lon=ds.longitude.values;lat=ds.latitude.values;plev=ds.isobaricInhPa.values;time=pd.to_datetime(ds.valid_time.values)


#%% Agrega variables de superficie antes del nivel mas superficial
sv=xr.open_dataset(rf'descargas_gfs/{fecha}_t00/gfs0p25_t00z_{fecha}_surface.nc') # carga variables de superficie

h_gl=sv.orog.values[0,:,:] # en metros, pasa la superficie a metros sobre el nivel del mar
#%%
H_agl = H - h_gl[np.newaxis,np.newaxis,:,:]


t_s=sv.t2m.values-273.15 # T2m en C
td_s=sv.d2m.values-273.15 # dewpoint en C
ws_s=((sv.u10.values**2+sv.v10.values**2)**0.5)*1.944 # rapidez del viento en nudos 
wd_s=np.mod(180+(180/np.pi) * np.arctan2(sv.u10.values,sv.v10.values) ,360) # direccion del viento
p_s=sv.sp.values/100 # presion superficial en hPa
from dewpoint import dewpoint
#----------- Parametrizaci�n del c�lculo punto a punto de los par�metros convectivos
from joblib import Parallel, delayed
def compute_cp(t):
    from rpy2.robjects.packages import importr
    from rpy2.robjects import r,pandas2ri
    import rpy2.robjects as robjects
    pandas2ri.activate()
    importr('thunder')
    cp_slice = np.full((len(lat), len(lon), 22), np.nan)
    for i in range(len(lat)):
        for j in range(len(lon)):
            ind_H = np.where(H_agl[t,:,i,j] > 0 )[0] # filtro para alturas mayores a 0
            T_d_aux=np.full(len(ind_H), np.nan)
            for a in range(len(ind_H)):
                T_d_aux[a]=dewpoint(T[t, ind_H[a],i,j]+273.15,rh=HR[t, ind_H[a],i,j]) - 273.15 #dewpoint entrega T en K
            # agrega valores de superficie a los perfiles verticales.
            plev_f=np.concatenate([[p_s[t,i,j]],plev[ind_H]])
            H_f=np.concatenate([[0],H_agl[t, ind_H, i, j]])
            T_f=np.concatenate([[t_s[t,i,j]],T[t, ind_H, i, j]])
            Td_f=np.concatenate([[td_s[t,i,j]],T_d_aux])
            w_speed_f=np.concatenate([[ws_s[t,i,j]],w_speed[t, ind_H, i, j]*1.944])
            w_dir_f=np.concatenate([[wd_s[t,i,j]],w_dir[t, ind_H, i, j]])
            cp_slice[i, j, :] = robjects.r['sounding_compute'](plev_f,
                H_f,T_f,Td_f, w_dir_f,w_speed_f,accuracy=2)[[0, 40, 90, 91, 92, 93, 94, 100, 101, 129, 130, 174, 7, 14, 47, 54, 57, 58, 59, 60, 68, 23]]
    return cp_slice
#%%

import time as tm
init= tm.time()
CP = Parallel(n_jobs=-1, verbose=10)(delayed(compute_cp)(t) for t in range(len(time)))
CP=np.array(CP)
end=tm.time()
print(f"Tiempo transcurrido: {end-init:.2f} segundos")

#%%
#%% Gráficos series de tiempo
# 0 = MUCAPE
# 3 = BS1km
# 9 = SRH_500m
# 11 = STP
# 13 = MULCL_HGT
# 15 = MLLCL_HGT
# 14 = MULCL_TEMP
# 16 = MLLCL_TEMP 
# 17 = LR_500m
# 18 = LR_1km 
CP_da = xr.DataArray(CP, coords=[time, lat, lon, np.arange(0,22)], dims=['time', 'lat', 'lon', 'parameter'])
dx = CP_da.to_dataset(name='ConvectiveParameters')
dx['mslp']=sv.mslp # guarda variable presion a niveld el mar
dx['geo500']=ds.gh[:,12,:,:] # guarda geopotencia a 500 metros
dx.to_netcdf(f'descargas_gfs/{fecha}_t00/CP_{fecha}.nc')

