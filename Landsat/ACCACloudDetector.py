#-------------------------------------------------------------------------------
# Name:        ACCA Cloud Detector
# Purpose:      To execute the Automated Cloud Cover Assesment algorithm on Landsat 7 imagery
#
# Author:      Quinten Geddes   Quinten.A.Geddes@nasa.gov
#               NASA DEVELOP Program
# Created:     13/02/2013

#-------------------------------------------------------------------------------
import arcpy
import math
import sys
from textwrap import dedent
from arcpy.sa import *
import DNtoReflectance
import numpy as np
from scipy import stats
import os
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

def ACCACloudDetector(L7bands, pixelvalue, OutputPath,MetaData="",SaveRefl=False,Filter5Thresh=2.0,Filter5Thresh=2.0):
    if pixelvalue=="Digital Numbers":
        for i,pathname in enumerate(L7bands):
            inputbandnum=str(["2","3","4","5","6"][i])
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
        ReflOutputFolder="\\".join(OutputPath.split("\\")[0:-1])

        Bands=DNtoReflectance.DNtoReflectance(L7bands,MetaData,Save=SaveRefl,OutputFolder=ReflOutputFolder)

        for i,raster in enumerate(Bands):
            if SaveRefl==True:
                exec("Band{0}=arcpy.Raster(raster)".format(["2","3","4","5","6"][i]))
            else:
                exec("Band{0}=raster".format(["2","3","4","5","6"][i]))

    elif pixelvalue=="Reflectance":
        for i,pathname in enumerate(L7bands):
            exec("Band{0}=arcpy.Raster(pathname)".format(["2","3","4","5","6"][i]))

    arcpy.AddMessage("Creating Gap Mask")
    print "Creating Gap Mask"
    #Establishing location of gaps in data. 0= Gap, 1=Data
    GapMask=((Band2>0)*(Band3>0)*(Band4>0)*(Band5>0)*(Band6>0))
    GapMask.save(OutputFolder+"\\GapMask.tif")

    arcpy.AddMessage("First pass underway")
    print "First pass underway"
    #Filter 1 - Brightness Threshold
    Cloudmask=Band3 >.08

    #filter 2 - Normalized Snow Difference Index
    NDSI=(Band2-Band5)/(Band2+Band5)
    Snow=(NDSI>.6)*Cloudmask
    Cloudmask=(NDSI<.6)*Cloudmask

    #filter 3 - Temperature Threshold
    Cloudmask=(Band6<300)*Cloudmask

    #filter 4 - Band 5/6 Composite
    Cloudmask=(((1-Band5)*Band6)<225)*Cloudmask
    Amb=(((1-Band5)*Band6)>225)

    #filter 5 - Band 4/3 Ratio (eliminates vegetation)
    #**bright cloud tops are sometimes cut out by this filter. original threshold was
    #2.0 this threshold was bumped to 2.5 to make algorithm more aggresive
    Cloudmask=((Band4/Band3)<Filter5Thresh)*Cloudmask
    Amb=((Band4/Band3)>Filter5Thresh)*Amb

    #filter 6 - Band 4/2 Ratio (eliminates vegetation)
    Cloudmask=((Band4/Band2)<Filter6Thresh)*Cloudmask
    Amb=((Band4/Band2)>Filter6Thresh)*Amb

    #filter 7 - Band 4/5 Ratio (Eliminates desert features)
    #   DesertIndex recorded
    DesertIndMask=((Band4/Band5)>1.0)
    Cloudmask=DesertIndMask*Cloudmask
    Amb=((Band4/Band5)<1.0)*Amb

    DesertGap=(DesertIndMask+1)*GapMask
    try:
        arcpy.CalculateStatistics_management(DesertGap,ignore_values="0")
        DesertIndex=DesertGap.mean-1
    except:
        DesertGap.save(OutputFolder+"\\Desert.tif")
        arcpy.CalculateStatistics_management(DesertGap,ignore_values="0")
        DesertIndex=DesertGap.mean-1
        os.remove(OutputFolder+"\\Desert.tif")
    del DesertIndMask, DesertGap, NDSI


    #Filter 8  Band 5/6 Composite (Seperates warm and cold clouds)
    WarmCloud=(((1-Band5)*Band6)>210)*Cloudmask
    ColdCloud=(((1-Band5)*Band6)<210)*Cloudmask


    ColdCloudGap=(ColdCloud+1)*GapMask
    try:
        arcpy.CalculateStatistics_management(ColdCloudGap,ignore_values="0")
        ColdCloudMean=ColdCloudGap.mean-1
        del ColdCloudGap
    except:
        ColdCloudGap.save(OutputFolder+"\\ColdCloud.tif")
        arcpy.CalculateStatistics_management(ColdCloudGap,ignore_values="0")
        ColdCloudMean=ColdCloudGap.mean-1
        os.remove(OutputFolder+"\\ColdCloud.tif")
        del ColdCloudGap

    del Band2,Band3,Band4,Band5


    #Determining whether or not snow is present and adjusting the Cloudmask
    #accordinging. If snow is present the Warm Clouds are reclassfied as ambigious


    SnowGap=(Snow+1)*GapMask
    try:
        arcpy.CalculateStatistics_management(SnowGap,ignore_values="0")
        SnowPerc=SnowGap.mean-1
        del SnowGap
    except:
        SnowGap.save(OutputFolder+"\\Snow.tif")
        arcpy.CalculateStatistics_management(SnowGap,ignore_values="0")
        SnowPerc=SnowGap.mean-1
        os.remove(OutputFolder+"\\Snow.tif")
        del SnowGap
    del Snow




    if SnowPerc>.01:
        SnowPresent=True
        Cloudmask=ColdCloud
        Amb=Amb+WarmCloud
    else:
        SnowPresent=False

    #Collecting statistics for Cloud pixel Temperature values. These will be used in later conditionals
    Tempclouds=Cloudmask*Band6

    Tempclouds.save(OutputFolder+"\\TempClouds.tif")

    Band6array=arcpy.RasterToNumPyArray(OutputFolder+"\\TempClouds.tif")

    del Tempclouds
    os.remove(OutputFolder+"\\TempClouds.tif")
    Band6clouds=Band6array[np.where(Band6array>0)]
    del Band6array
    TempMin=Band6clouds.min()
    TempMax=Band6clouds.max()
    TempMean=Band6clouds.mean()
    TempStd=Band6clouds.std()
    TempSkew=stats.skew(Band6clouds)
    Temp98perc=stats.scoreatpercentile(Band6clouds, 98.75)
    Temp97perc=stats.scoreatpercentile(Band6clouds, 97.50)
    Temp82perc=stats.scoreatpercentile(Band6clouds, 82.50)
    del Band6clouds

    #Pass 2 is run if the following conditionals are met
    if ColdCloudMean>.004 and DesertIndex>.5 and TempMean<295:
        #Pass 2
        arcpy.AddMessage("Second Pass underway")

        #Adjusting Temperature thresholds based on skew
        if TempSkew>0:
            if TempSkew>1:
                shift=TempStd
            else:
                shift = TempStd*TempSkew
        else: shift=0
        Temp97perc+=shift
        Temp82perc+=shift
        if Temp97perc>Temp98perc:
            Temp82perc=Temp82perc-(Temp97perc-Temp98perc)
            Temp97perc=Temp98perc

        warmAmbmask=((Band6*Amb)<Temp97perc)
        warmAmbmask=warmAmbmask*((Amb*Band6)>Temp82perc)

        coldAmbmask=(Band6*Amb)<Temp82perc
        coldAmbmask=coldAmbmask*((Amb*Band6)>0)

        warmAmb=warmAmbmask*Band6
        coldAmb=coldAmbmask*Band6

        ThermEffect1=warmAmbmask.mean
        ThermEffect2=coldAmbmask.mean

        arcpy.CalculateStatistics_management(warmAmb,ignore_values="0")
        arcpy.CalculateStatistics_management(coldAmb,ignore_values="0")

        if ThermEffect1<.4 and warmAmb.mean<295 and SnowPresent==False:
            Cloudmask=Cloudmask+warmAmbmask+coldAmbmask
            arcpy.AddMessage("Upper Threshold Used")
        elif ThermEffect2<.4 and coldAmb.mean<295:
            Cloudmask=Cloudmask+coldAmbmask
            arcpy.AddMessage("Lower Threshold Used")

    #switch legend to 1=good data 0 = cloud pixel
    Cloudmask=(Cloudmask*GapMask)==0

    Cloudmask.save(OutputFolder+"\\"+OutputFileName)
    del Cloudmask,GapMask

    os.remove(OutputFolder+"\\GapMask.tif")
    return Cloudmask