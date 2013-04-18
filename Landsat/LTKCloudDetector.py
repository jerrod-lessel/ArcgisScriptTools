#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      qgeddes
#
# Created:     15/02/2013
# Copyright:   (c) qgeddes 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from glob import glob
import arcpy
arcpy.env.overwriteOutput = True
import sys
import os
import math
arcpy.CheckOutExtension("Spatial")
#Band1path="C:\\Users\\qgeddes\\Downloads\\Landsat\\Cloudtest\\Alabama\\LE70190392012129EDC00_B1.TIF"
#Band3path="C:\\Users\\qgeddes\\Downloads\\Landsat\\Cloudtest\\Alabama\\LE70190392012129EDC00_B3.TIF"
#Band4path="C:\\Users\\qgeddes\\Downloads\\Landsat\\Cloudtest\\Alabama\\LE70190392012129EDC00_B4.TIF"
#Band5path="C:\\Users\\qgeddes\\Downloads\\Landsat\\Cloudtest\\Alabama\\LE70190392012129EDC00_B5.TIF"
#pixelvalue="Digital Numbers"
Band1path=arcpy.GetParameterAsText(0)
Band3path=arcpy.GetParameterAsText(1)
Band4path=arcpy.GetParameterAsText(2)
Band5path=arcpy.GetParameterAsText(3)

pixelvalue=arcpy.GetParameterAsText(4)
MetaData=arcpy.GetParameterAsText(5)
OutputFolder=arcpy.GetParameterAsText(6)
OutputFileName=arcpy.GetParameterAsText(7)

L7bands=[Band1path,Band3path,Band4path,Band5path]

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
    else:
        Meta=newMeta
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


    #Calculating values for each band
    BandNum=0

    for i,pathname in enumerate(L7bands):
        inputbandnum=str(["1","3","4","5"][i])
        try:
            BandNum=pathname.split("\\")[-1].split("_B")[1][0]
        except:
            sys.exit("Error reading Band {0}. Bands must have original names as downloaded.".format(str(inputbandnum)))
        if BandNum!=inputbandnum:
            sys.exit("Error reading Band {0}. Bands must have original names as downloaded. The inputed file appears to actually be Band {1} data".format(inputbandnum,BandNum))

        f=open(MetaData)
        text=f.read()
        Oraster=arcpy.Raster(pathname)
        LMax=   float(text.split(Meta[3].format(BandNum))[1].split("\n")[0])
        LMin=   float(text.split(Meta[4].format(BandNum))[1].split("\n")[0])
        QCalMax=float(text.split(Meta[5].format(BandNum))[1].split("\n")[0])
        QCalMin=float(text.split(Meta[6].format(BandNum))[1].split("\n")[0])

        Radraster=(((LMax - LMin)/(QCalMax-QCalMin)) * (Oraster - QCalMin)) +LMin
        Oraster=0


        Refraster=( math.pi * Radraster * dSun2) / (ESun[int(BandNum[0])-1] * math.cos(SZA*math.pi/180) )
        exec("Band{0}=Refraster".format(BandNum))
        del Refraster
        arcpy.AddMessage( "Band {0} Converted to Reflectance".format(BandNum))
        Radraster=0
        f.close()
    arcpy.AddMessage("Reflectance calculated. Executing Algorithm")


elif pixelvalue=="Reflectance":
    for i,pathname in enumerate(L7bands):
        exec("Band{0}=arcpy.Raster(pathname)".format(["1","3","4","5"][i]))
arcpy.AddMessage("Creating Gap Mask")
##GapMask=

arcpy.AddMessage("Beginning LTK algorithm")
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

#set all cloud pixels to "NODATA" and all other pixels to 1
CloudMask=arcpy.sa.Abs(Clouds-1)

CloudMask.save(OutputFolder+"\\"+OutputFileName)