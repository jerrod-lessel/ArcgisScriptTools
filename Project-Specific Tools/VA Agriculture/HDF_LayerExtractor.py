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

#These are the spatial reference parameters that are specific to this grid
#these parameters will be used to georeference the image
cellSize=926.6254331

#this is the Well Known Text for the MODIS Sinusoidal Projection
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

#this point represtents the left-bottom corner of the dataset
pnt=arcpy.Point(-7470454.24127,4062325.89888)

#for each index provided by the Layer List parameter
for i in layers:
    outputfilename="{0}\\{1}{2}.tif".format(outputfolder,outputprefix,i)
    #attaining the data array from the input .h5 file
    data=f[harray][:,:,(int(i)-1)]


    #converting the array to an arcpy Raster object
    #the corner point and cellSize information is used here
    output=arcpy.NumPyArrayToRaster(data,pnt, cellSize,cellSize)

    #defining the output raster's projection as MODIS Sinusoidal
    arcpy.DefineProjection_management(output, sr)
##
##    -----------------------
##    Extra functions can be added here
##
##    ------------------------

    #if exclude Zero is true. Zeros are converted to nodata
    if excludeZero==True:
        arcpy.CopyRaster_management(output,outputfilename,nodata_value=0)
    else:
        #calculating statisitcs in order to reset color table
        arcpy.CalculateStatistics_management(output)
        output.save(outputfilename)

    arcpy.AddMessage(i)

