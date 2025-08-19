#!/bin/bash
source ~/.bashrc
conda activate data-science
cd /home/cr2/jcampos/ConvectiveParameters_ForecastGFS


fecha=`date -u +%Y%m%d`
#echo $fecha
python get_GFS_forecast.py --var ${fecha} # descarga archivos GFS y genera 2 netcdf

python CP_forecast.py --var ${fecha} # calcula parametros convectivos a partir de GFS

python CP_grafico.py --var ${fecha} # genera un gif de la evolucion temporal de CAPE, BS, SRH, STP



