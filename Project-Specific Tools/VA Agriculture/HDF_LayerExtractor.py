#-------------------------------------------------------------------------------
# Name:        Layer extractor
# Purpose:
#
# Author:      qgeddes
#
# Created:     22/03/2013
# Copyright:   (c) qgeddes 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
import numpy as np
from osgeo import gdal
import h5py
from math import pi

hfile=arcpy.GetParameterAsText(0)
harray=arcpy.GetParameterAsText(1)
layerlist=arcpy.GetParameterAsText(2)
outputfolder=arcpy.GetParameterAsText(3)
outputprefix=arcpy.GetParameterAsText(4)
excludeZero=arcpy.GetParameterAsText(4)
layers=layerlist.split(";")

f=h5py.File(hfile)

src=gdal.Open("C:\\Users\\qgeddes\\Downloads\\VAwinery\\LST_MODIS_Aqua\\Analysis\\ReferenceTemplate.tif")
driver=gdal.GetDriverByName("GTiff")

cols,rows=src.RasterXSize,src.RasterYSize

for day in layers:
    #creating output files

    outfile=driver.CreateCopy("{0}\\{1}{2}.tif".format(outputfolder,outputprefix,day),src,0)

    #attaining the original array and deriving the bad pixel info and masking the original

    data=f[harray][:,:,(int(day)-1)]


    #writing the arrays to the output raster and setting the null values
    outfile.GetRasterBand(1).WriteArray(data)
    if excludeZero=="true":
        outfile.GetRasterBand(1).SetNoDataValue(0)

    outfile=0
    #calculating statisitcs in order to reset color table
    arcpy.CalculateStatistics_management("{0}\\{1}{2}.tif".format(outputfolder,outputprefix,day))

    arcpy.AddMessage(day)

