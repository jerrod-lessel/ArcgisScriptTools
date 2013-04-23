#-------------------------------------------------------------------------------
# Name:        ACCA Cloud Detector
# Purpose:      To execute the Automated Cloud Cover Assesment algorithm on Landsat 7 imagery
#
# Author:      Quinten Geddes   Quinten.A.Geddes@nasa.gov
#               NASA DEVELOP Program
# Created:     13/02/2013

#-------------------------------------------------------------------------------
from glob import glob
import arcpy
import math
import sys
from textwrap import dedent
from arcpy.sa import *
arcpy.env.overwriteOutput = True


try:
    import numpy as np

except:
    msg="""
    The NumPy module is need for this tool. The module can be downloaded at the following address:
    http://sourceforge.net/projects/numpy/files/NumPy/1.6.2
    Download the appropriate superpack installer for windows for your Python version
    ArcGIS 10   uses Python 2.6
    ArcGIS 10.1 uses Python 2.7"""
    arcpy.AddError(dedent(msg))
    raise arcpy.ExecuteError
try:
    from scipy import stats
except:
    msg="""
    The SciPy module is need for this tool. The module can be downloaded at the following address:
    http://sourceforge.net/projects/scipy/files/scipy/0.11.0
    Download the appropriate superpack installer for windows for your Python version
    ArcGIS 10   uses Python 2.6
    ArcGIS 10.1 uses Python 2.7"""
    arcpy.AddError(dedent(msg))
    raise arcpy.ExecuteError

import os
arcpy.CheckOutExtension("Spatial")

Band2path=      arcpy.GetParameterAsText(0)
Band3path=      arcpy.GetParameterAsText(1)
Band4path=      arcpy.GetParameterAsText(2)
Band5path=      arcpy.GetParameterAsText(3)
Band6path=      arcpy.GetParameterAsText(4)

pixelvalue=     arcpy.GetParameterAsText(5)
MetaData=       arcpy.GetParameterAsText(6)
OutputFolder=   arcpy.GetParameterAsText(7)
OutputFileName= arcpy.GetParameterAsText(8)

Filter5Thresh=float(arcpy.GetParameterAsText(9))
Filter6Thresh=float(arcpy.GetParameterAsText(10))

L7bands=[Band2path,Band3path,Band4path,Band5path,Band6path]

#checking if the file extension is appropriate and making alterations if necessary
FileNameSplit=OutputFileName.split(".")
if FileNameSplit[-1] not in ["tif","img"]:
    arcpy.AddWarning("Output Image must be saved in either the .tif or .img file format. Sorry, blame Esri. File has been change to .tif")
    if len(FileNameSplit)==1:
        OutputFileName+=".tif"
    else:
        FileNameSplit[-1]="tif"
        OutputFileName=".".join(FileNameSplit)

arcpy.env.scratchWorkspace=OutputFolder

if pixelvalue=="Digital Numbers":
    arcpy.AddMessage("Calculating Reflectance...")
    newMeta=['LANDSAT_SCENE_ID = "','DATE_ACQUIRED = ',"SUN_ELEVATION = ",
                "RADIANCE_MAXIMUM_BAND_{0} = ","RADIANCE_MINIMUM_BAND_{0} = ",
                "QUANTIZE_CAL_MAX_BAND_{0} = ","QUANTIZE_CAL_MIN_BAND_{0} = "]

    oldMeta=['BAND1_FILE_NAME = "',"ACQUISITION_DATE = ","SUN_ELEVATION = ",
                "LMAX_BAND{0} = ","LMIN_BAND{0} = ",
                "QCALMAX_BAND{0} = ","QCALMIN_BAND{0} = "]
    f=open(MetaData)

    MText=f.read()

    if "PRODUCT_CREATION_TIME" in MText:
        Meta=oldMeta
        Band6length=2
    else:
        Meta=newMeta
        Band6length=8
    if Meta==newMeta:
        TileName=MText.split(Meta[0])[1].split('"')[0]
        year=TileName[9:13]
        jday=TileName[13:16]
    elif Meta==oldMeta:
        TileName=MText.split(Meta[0])[1].split('"')[0]
        year=TileName[13:17]
        jday=TileName[17:20]

    date=MText.split(Meta[1])[1].split('\n')[0]
    L7_ESun=(1969.0,1840.0,1551.0,1044.0,255.700,0.,82.07,1368.00)
    L5_ESun=(1957.0,1826.0,1554.0,1036.0,215.0  ,0.,80.67)
    spacecraft=MText.split('SPACECRAFT_ID = "')[1].split('"')[0]

    if "7" in spacecraft:
        ESun=L7_ESun
    if spacecraft[8]=="5":
        ESun=L5_ESun
    if float(year) % 4 ==0:
        DIY=366.
    else:
        DIY=365.
    theta =2*math.pi*float(jday)/DIY

    dSun2 = 1.00011 + 0.034221*math.cos(theta) + 0.001280*math.sin(theta) + 0.000719*math.cos(2*theta)+ 0.000077*math.sin(2*theta)

    SZA=90.-float(MText.split(Meta[2])[1].split("\n")[0])


    #Calculating Reflectance values for each band
    BandNum=0

    for i,pathname in enumerate(L7bands):
        inputbandnum=["2","3","4","5","6"][i]
        try:
            BandNum=pathname.split("\\")[-1].split("_B")[1][0]
            if BandNum=="6" and spacecraft[8]=="7":
                BandNum=pathname.split("\\")[-1].split("_B")[1][0:Band6length]
        except:
            arcpy.AddError(dedent("""
                                  -------------
                                  ERROR reading Band {0}. Bands must have original names as downloaded.
                                  -------------""".format(str(inputbandnum))))
            raise arcpy.ExecuteError
        if BandNum[0]!=inputbandnum:
            msg=dedent("""
                       ERROR reading Band {0}. Bands must have original names as downloaded.
                       The inputed file appears to actually be Band {1} data
                       """.format(inputbandnum,BandNum))
            arcpy.AddError(msg)
            raise arcpy.ExecuteError
        arcpy.AddMessage( "Processing Band {0}".format(BandNum))
        f=open(MetaData)
        text=f.read()
        Oraster=arcpy.Raster(pathname)

        LMax=   float(text.split(Meta[3].format(BandNum))[1].split("\n")[0])
        LMin=   float(text.split(Meta[4].format(BandNum))[1].split("\n")[0])
        QCalMax=float(text.split(Meta[5].format(BandNum))[1].split("\n")[0])
        QCalMin=float(text.split(Meta[6].format(BandNum))[1].split("\n")[0])

        Radraster=(((LMax - LMin)/(QCalMax-QCalMin)) * (Oraster - QCalMin)) +LMin
        Oraster=0

        if "6" in BandNum:
            TempKraster=1282.71/(arcpy.sa.Ln((666.09/Radraster)+1.0))
            Band6=Con(IsNull(TempKraster),0,TempKraster)
            del TempKraster

        else:
            Refraster=( math.pi * Radraster * dSun2) / (ESun[int(BandNum[0])-1] * math.cos(SZA*math.pi/180) )
            exec("Band{0}=Refraster".format(BandNum))
            del Refraster


        Radraster=0
        f.close()
    arcpy.AddMessage("Reflectance calculated. Executing Algorithm")


elif pixelvalue=="Reflectance":
    for i,pathname in enumerate(L7bands):
        exec("Band{0}=arcpy.Raster(pathname)".format(["2","3","4","5","6"][i]))

arcpy.AddMessage("Creating Gap Mask")

#Establishing location of gaps in data. 0= Gap, 1=Data
GapMask=((Band2>0)*(Band3>0)*(Band4>0)*(Band5>0)*(Band6>0))
GapMask.save(OutputFolder+"\\GapMask.tif")

arcpy.AddMessage("First pass underway")
#Filter 1 - Brightness Threshold
Cloudmask=Band3 >.08

#filter 2 - Normalized Snow Difference Index
NDSI=(Band2-Band5)/(Band2+Band5)
Snow=(NDSI>.6)*Cloudmask
Cloudmask=(NDSI<.6)*Cloudmask

del NDSI

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
    del DesertGap
except:
    DesertGap.save(OutputFolder+"\\Desert.tif")
    arcpy.CalculateStatistics_management(DesertGap,ignore_values="0")
    DesertIndex=DesertGap.mean-1
    del DesertGap
    os.remove(OutputFolder+"\\Desert.tif")
del DesertIndMask


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
        arcpy.AddMessage("Upper Threshold Uused")
    elif ThermEffect2<.4 and coldAmb.mean<295:
        Cloudmask=Cloudmask+coldAmbmask
        arcpy.AddMessage("Lower Threshold Used")

#switch legend to 1=good data 0 = cloud pixel
Cloudmask=(Cloudmask*GapMask)==0

Cloudmask.save(OutputFolder+"\\"+OutputFileName)
del Cloudmask,GapMask

os.remove(OutputFolder+"\\GapMask.tif")
arcpy.CheckInExtension("Spatial")