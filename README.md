# Convective-Parameters-GFS-forecast
Download GFS forecast variables to compute Convective Parameters in a desire domain. It create a netcdf file of convective parameters and a gif animation of the forecast.

There are 4 python scripts. The bash script "run_CP_forecast.sh" runs all the python files in the correct order to generate the corresponding directories, netcdf files and gifs. 
When you run the .sh file it creates a directory with today's date with 3 netcdf files: CP_{date}.nc (convective parameters), gfs0p25_t00z_{date}_pl.nc (pressure levels), gfs0p25_t00z_{date}_surface.nc (surface levels). 

Python files:

1 - get_GFS_forecast.py :  Download the GFS files from today's date and make the 2 netcdf files. Can set the step and max_time. 

2 - CP_forecast.py : Computes the convective parameters from the GFS netcdf files and make a Convective Parameter netcdf file.

3 - CP_grafico.py : Makes the gif animation from the CP netcdf file.
