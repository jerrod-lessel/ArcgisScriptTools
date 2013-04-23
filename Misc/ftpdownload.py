#-------------------------------------------------------------------------------
# Name:        Reverb Echo FTP downloader
# Purpose:      To read the text files with ftp addresses aquired from the Echo Reverb site
#
# Author:       Quinten Geddes    Quinten.A.Geddes@nasa.gov
#                   NASA DEVELOP Program
# Created:     22/03/2013

#-------------------------------------------------------------------------------

import urllib
import arcpy

ftptext= arcpy.GetParameterAsText(0)
output = arcpy.GetParameterAsText(1)

ftp = open(ftptext,'r')

a =ftp.readlines()
b=[]
for i in a:
    i.split("=")
for site in a:
    url = site.rstrip()
    sub = url.split("/")
    leng = len(sub)
    name = sub[leng-1]
    if ".hdf" in sub[leng-1]:
        try:
            urllib.urlretrieve(url, output+"\\"+sub[leng-1])
            arcpy.AddMessage(sub[leng-1]+ "  is downloaded")
        except:
            arcpy.AddMessage((sub[leng-1]+ "  failed to download"))
