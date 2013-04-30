#-------------------------------------------------------------------------------
# Name:        LTK Cloud Detector
# Purpose:      To execute the LTK cloud detection algorithm on Landsat 7 imagery
#
# Author:      Quinten Geddes     Quinten.A.Geddes
#               NASA DEVELOP Progra,
# Created:     15/02/2013

#-------------------------------------------------------------------------------
from glob import glob
import arcpy
arcpy.env.overwriteOutput = True
import sys
import os
import math
import tempfile
import DNtoReflectance
from textwrap import dedent
arcpy.CheckOutExtension("Spatial")

def LTKCloudDetector(Bands1345, pixelvalue, OutputPath,MetaData="",SaveRefl=False,ReflOutputFolder=""):
    """using Landsat 7 bands 1, 3, 4, and 5 to detect cloud using the LTK
    cloud cover classification algorithm"""

    #checking if the file extension is appropriate and making alterations if necessary
    FileNameSplit=OutputPath.split(".")
    if FileNameSplit[-1] not in ["tif","img"]:
        msg=dedent("""
        Output Image must be saved in either the .tif or .img file format.
        File has been change to .tif""")
        arcpy.AddWarning(msg)
        print msg
        if len(FileNameSplit)==1:
            OutputFileName+=".tif"
        else:
            FileNameSplit[-1]="tif"
            OutputFileName=".".join(FileNameSplit)


    if pixelvalue=="Digital Numbers":
        for i,pathname in enumerate(Bands1345):
            inputbandnum=str(["1","3","4","5"][i])
            try:
                BandNum=pathname.split("\\")[-1].split("_B")[1][0]
            except:
                msg=dedent("""
                Error reading Band {0}.
                Bands must have original names as downloaded.""".format(str(inputbandnum)))
                arcpy.AddError(msg)
                print msg
                raise arcpy.ExecuteError
            if BandNum!=inputbandnum:
                msg=dedent("""
                Error reading Band {0}.
                Bands must have original names as downloaded.
                The inputed file appears to actually be Band {1} data""".format(inputbandnum,BandNum))
                arcpy.AddError(msg)
                print msg
                raise arcpy.ExecuteError
        if not ReflOutputFolder:
            ReflOutputPath="\\".join(OutputPath.split("\\")[0:-1])
        else:
            ReflOutputPath=ReflOutputFolder
        Bands=DNtoReflectance.DNtoReflectance(Bands1345,MetaData,Save=SaveRefl,OutputFolder=ReflOutputPath)

        for i,raster in enumerate(Bands):
            if SaveRefl==True:
                exec("Band{0}=arcpy.Raster(raster)".format(["1","3","4","5"][i]))
            else:
                exec("Band{0}=raster".format(["1","3","4","5"][i]))


    elif pixelvalue=="Reflectance":
        for i,pathname in enumerate(Bands1345):
            exec("Band{0}=arcpy.Raster(pathname)".format(["1","3","4","5"][i]))
    arcpy.AddMessage("Creating Gap Mask")
    print "Creating Gap Mask"

    GapMask=((Band1>0)*(Band3>0)*(Band4>0)*(Band5>0))

    arcpy.AddMessage("Beginning LTK algorithm")
    print "Beginning LTK algorithm"

    #Begin of LTK Algorithm---------------------------------------------------------
    #filter 1
    nonveglands=(Band1<Band3)*(Band3<Band4)*(Band4<(Band5*1.07))*(Band5<.65)
    nonveglands=((Band1*.8)<Band3)*(Band3<(.8*Band4))*(Band4<Band5)*(Band3<.22)+nonveglands
    nonveglands=nonveglands>0
    Amb=nonveglands==0

    #filter 2
    SnowIce=Amb*((Band3>.24)*(Band5<.16)*(Band3>Band4))
    SnowIce=SnowIce+((.24>Band3)*(Band3>.18)*(Band5<(Band3-.08))*(Band3>Band4))
    SnowIce=SnowIce>0
    Amb=Amb*(SnowIce==0)

    #filter 3
    Water=Amb*(Band3>Band4)*(Band3>(.67*Band5))*(Band1<.30)*(Band3<.20)
    Water=Water+(Band3>(.8*Band4))*(Band3>(Band5*.67))*(Band3<.06)
    Water=Water>0
    Amb=Amb*(Water==0)

    #filter 4
    maxB1_B3=((Band1>=Band3)*Band1)+((Band3>Band1)*Band3)
    Clouds=Amb*( (((Band1>.15)+(Band3>.18))>0) * (Band5>.12)* (maxB1_B3>(Band5*.67)))

    #set all cloud pixels to 0 and all good pixels to 1. And apply the gap mask
    CloudMask=((Clouds*GapMask)==0)

    CloudMask.save(OutputPath)

    return OutputPath