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

fecha=var
ds=xr.open_dataset(f'descargas_gfs/{fecha}_t00/CP_{fecha}.nc')
lat=ds.lat; lon=ds.lon; CP=ds.ConvectiveParameters; time=ds.time
CP=ds.ConvectiveParameters

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import imageio.v2 as imageio
import pandas as pd

time_dim = CP.shape[0]
lon_dim, lat_dim = lon.shape[0], lat.shape[0]


# Crear carpeta temporal para imagenes
output_folder = "temp_frames"
os.makedirs(output_folder, exist_ok=True)

# indices de los niveles a graficar
niveles = [0, 3, 9, 11]
# rangos de las colorbar para cada viarbale
rangos=[[50,500],[10,24],[-400,-100],[-0.5,-0.01]]
names=["MUCAPE", "BS_01km", "SRH500m_LM", "STP"]
units=["[J/kg]", "[m/s]", "[m2/s2]", ""]

step=3
filenames = []

for t in range(time_dim):
    fig, axes = plt.subplots(2, 2, figsize=(8, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    fig.suptitle(f"Convective Parameters - GFS forecast \n init: {pd.to_datetime(time[0].values).strftime('%Y-%m-%dT%H:%M:%S')} -- f{t*step:03} \n valid_time: {pd.to_datetime(time[t].values).strftime('%Y-%m-%dT%H:%M:%S')}", fontsize=16)
    axes = axes.flatten()
    for i in range(4):
        ax = axes[i]
        ax.coastlines(resolution='10m')
        gl=ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        ax.set_extent([-85,-70,-55,-30])
        gl.top_labels=False
        gl.right_labels=False
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        data = CP[t, :, :, niveles[i]]
        if i in [0, 1]:
            vmin, vmax = rangos[i][0], rangos[i][1]
            im = ax.contourf(lon, lat, data, cmap='jet', levels=np.linspace(vmin,vmax,11), extend='max')
        elif i in [2, 3]:
            vmin, vmax = rangos[i][0], rangos[i][1]
            im = ax.contourf(lon, lat, data, cmap='jet_r',levels=np.linspace(vmin,vmax,11), extend='min')
        cnt=ax.contour(lon,lat,ds.mslp[t,:,:]/100, colors='k',alpha=0.4, linewidths=0.6 )
        ax.clabel(cnt,fontsize=7)
        cbar = fig.colorbar(im, ax=ax, orientation='vertical')
        cbar.set_label(f"{names[i]} {units[i]}")
    filename = os.path.join(output_folder, f"frame_{t:03d}.png")
    plt.savefig(filename)
    filenames.append(filename)
    plt.close()
    print(t)

dest_folder=f"descargas_gfs/{fecha}_t00"
with imageio.get_writer(f"{dest_folder}/forecastCPs_{fecha}.gif", mode='I', fps=1) as writer:
    for filename in filenames:
        image = imageio.imread(filename)
        writer.append_data(image)

# Eliminar imagenes temporales (opcional)
for filename in filenames:
    os.remove(filename)
os.rmdir(output_folder)
