# Convective-Parameters-GFS-forecast
Download GFS forecast variables to compute Convective Parameters in a desire domain. It create a netcdf file of convective parameters and a gif animation of the forecast.

There are 4 python scripts. The bash script "run_CP_forecast.sh" runs all the python files in the correct order to generate the corresponding directories, netcdf files and gifs. 
When you run the .sh file it creates a directory with today's date with 3 netcdf files: CP_{date}.nc (convective parameters), gfs0p25_t00z_{date}_pl.nc (pressure levels), gfs0p25_t00z_{date}_surface.nc (surface levels). 

Python files:

1 - get_GFS_forecast.py

2 - CP_forecast.py

3 - CP_grafico.py
