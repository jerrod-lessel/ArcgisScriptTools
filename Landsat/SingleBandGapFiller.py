#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      qgeddes
#
# Created:     12/04/2013
# Copyright:   (c) qgeddes 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput=True

Scene1    =   arcpy.Raster(arcpy.GetParameterAsText(0))
Scene2    =   arcpy.Raster(arcpy.GetParameterAsText(1))
Scene3    =   arcpy.Raster(arcpy.GetParameterAsText(2))

CloudMaskpath1=   arcpy.GetParameterAsText(3)
CloudMaskpath2=   arcpy.GetParameterAsText(4)
CloudMaskpath3=   arcpy.GetParameterAsText(5)

OutputFolder= arcpy.GetParameterAsText(6)
OutputFile=   arcpy.GetParameterAsText(7)

arcpy.env.scratchWorkspace=OutputFolder


Mask1=Scene1>0
Mask2=Scene2>0
Mask3=Scene3>0
for scene in [1,2,3]:
    try:
        exec("CloudMask{0}=arcpy.Raster(CloudMaskpath{0})".format(scene))
        exec("Mask{0}=Mask{0}*CloudMask{0}".format(scence))
    except:
        a=0

#where nodata is present for first scene and data is present for second
Scene1Fill=Mask1*Scene1
Scene2Fill=((Mask1==0)*Mask2)*Scene2
Scene3Fill=((Mask1==0)*(Mask2==0)*Mask3)*Scene3
FinalImage=Scene1Fill+Scene2Fill+Scene3Fill


FinalImage.save(OutputFolder+"\\"+OutputFile)
