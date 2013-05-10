#-------------------------------------------------------------------------------
# Name:        HDF Layer Extractor
# Purpose:      To extract layers from HDF files created for the 2013 VA Agriculture project
#
# Author:       Quinten Geddes    Quinten.A.Geddes@nasa.gov
#                   NASA DEVELOP Program
# Created:     22/03/2013

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
excludeZero=arcpy.GetParameter(5)
layers=layerlist.split(";")

f=h5py.File(hfile)

arcpy.CheckOutExtension("Spatial")
cellSize=926.6254331
sr= """PROJCS["Sinusoidal",
            GEOGCS["GCS_Undefined",
                DATUM["D_Undefined",
                    SPHEROID["User_Defined_Spheroid",6371007.181,0.0]],
                PRIMEM["Greenwich",0.0],
                UNIT["Degree",0.017453292519943295]],
            PROJECTION["Sinusoidal"],
            PARAMETER["False_Easting",0.0],
            PARAMETER["False_Northing",0.0],
            PARAMETER["Central_Meridian",0.0],
            UNIT["Meter",1.0]]"""

pnt=arcpy.Point(-7470454.24127,4062325.89888)

for day in layers:
    #creating output files

    #attaining the original array and deriving the bad pixel info and masking the original

    data=f[harray][:,:,(int(day)-1)]


    #writing the arrays to the output raster and setting the null values
    output=arcpy.NumPyArrayToRaster(data,pnt, cellSize,cellSize)
    arcpy.DefineProjection_management(output, sr)

    #calculating statisitcs in order to reset color table
    arcpy.CalculateStatistics_management(output)
    if excludeZero==True:
        output=arcpy.sa.Con(output,output,where_clause="NOT VALUE=0")
    output.save("{0}\\{1}{2}.tif".format(outputfolder,outputprefix,day))
    arcpy.AddMessage(day)

