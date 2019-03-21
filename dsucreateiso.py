#!/usr/bin/python

# The MIT License (MIT)
#
# Copyright 2016 DellEMC Inc.  All Rights Reserved.
#
# PERMISSION IS HEREBY GRANTED, FREE OF CHARGE,
# TO ANY PERSON OBTAINING A COPY OF THIS SOFTWARE
# AND ASSOCIATED DOCUMENTATION FILES (THE "SOFTWARE"),
# TO DEAL IN THE SOFTWARE WITHOUT RESTRICTION,
# INCLUDING WITHOUT LIMITATION THE RIGHTS TO
# USE, COPY, MODIFY, MERGE, PUBLISH, DISTRIBUTE,
# SUBLICENSE, AND/OR SELL COPIES OF THE SOFTWARE,
# AND TO PERMIT PERSONS TO WHOM THE SOFTWARE IS
# FURNISHED TO DO SO, SUBJECT TO THE FOLLOWING
# CONDITIONS:
#
# THE ABOVE COPYRIGHT NOTICE AND THIS PERMISSION
# NOTICE SHALL BE INCLUDED IN ALL COPIES OR
# SUBSTANTIAL PORTIONS OF THE SOFTWARE.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT
# WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
# THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import os.path
import sys
import stat
import hashlib
import errno
import traceback
import shutil
import datetime
import tempfile
import urllib2
import logging
import gzip
import re
import imp
import tarfile


from xml.dom import minidom
from optparse import OptionParser, OptionGroup
from contextlib import contextmanager
from collections import defaultdict
from xml.dom.minidom import getDOMImplementation

try:
    imp.find_module('lxml')
    foundlxmlmodule = True
    from lxml import etree
except ImportError:
    foundlxmlmodule = False
    pass


def hash_file(filename):
    """"This function returns the SHA-1 hash
    of the file passed into it"""

    # make a hash object
    h = hashlib.md5()

    # open file for reading in binary mode
    with open(filename, 'rb') as file:
        # loop till the end of the file
        chunk = 0
        while chunk != b'':
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def mkdir_p(path):
    try:
        os.makedirs(path)
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
            return False
    return True


class TemporaryDirectory(object):
    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self.name

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.name)
        dsulog("cleaning up "+ self.name,False)


class GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def isWritable(filepath):
    try:
        testfile = open(filepath, 'w')
        testfile.close()
        os.remove(filepath)
        return True
    except IOError as e:
        return False
    return True

def isdiskFull(path, filesize):
    spaceInfo  = os.statvfs(path)
    availableSpace = (spaceInfo.f_bavail * spaceInfo.f_frsize) / 1024
    dsulog("Available space in Kb for dir " + path + ": " + str(availableSpace) + ". Required is "+ str(filesize), False)
    if filesize < availableSpace:
        return False
    dsulog("Not enough space available", False)
    return True


def dsulog(msg, isUserMsg):
    if logEnable:
        if isUserMsg:
            if disablePrintToConsole:
                logging.info(msg)
            else:
                logging.info(msg)
                print msg
        else:
            logging.debug(msg)
    elif isUserMsg:
        print msg


def verifyFile(repositoryRoot, softwareComponent):
    pathAttr = softwareComponent.getAttribute("path")
    md5 = softwareComponent.getAttribute("hashMD5")
    filepath = os.path.join(repositoryRoot, pathAttr)
    filehash = ""
    if not os.path.isfile(filepath):
        dsulog("File MISSING:\t" + filepath + "\n", False)
        return -1
    else:
        filehash = hash_file(filepath).upper()
        if (md5.upper() != filehash):
            dsulog("MD5 MISMATCH:\t" + filepath + ":expected=" + md5 + " actual=" + filehash + "\n", False)
            return -2

    return 0


def getFileExtension(filePath):
    filename, file_extension = os.path.splitext(filePath)
    return file_extension


def extractTARGZ(targzFilePath):
    try:
        tar = tarfile.open(targzFilePath)
        tar.extractall(tempdir)
        tar.close()
        return True
    except:
        e = sys.exc_info()
        dsulog("Exception: " + str(e) + "\n", False)
        return False



def extractGZ(gzFilePath, destinationFilePath, isFile):
    if isValidPath(destinationFilePath, True):
        dsulog("Deleting any previous file: " + destinationFilePath, False)
        dsulog(">>>>>>>>>>>>>>>>>>>>>> rm log start", False)
        ret = os.system("rm -f " + "\"" +  destinationFilePath + "\"" )
        dsulog("<<<<<<<<<<<<<<<<<<<<<< rm log end", False)
        dsulog("ret=" + str(ret), False)
    try:
        dsulog("Extracting catalog: "+ os.path.basename(gzFilePath), True)
        gzFile = gzip.open(gzFilePath,'rb')
        gzFileContent = gzFile.read()
        gzFile.close()
        f = open(destinationFilePath, "w")
        f.write(gzFileContent)
        f.close()
        return True

    except IOError as e:
        dsulog("Catalog Extraction Failed. " + str(e) , False)
        dsulog("Extraction failed. Supported format is gz" , True)
        return False

    return True

def displayPlatformInfo(catalogFile, displayToConsole):
    listOfAvailablePlatforms = defaultdict(dict)
    linuxbundlefound= False
    for sb in catalogFile.getElementsByTagName("SoftwareBundle"):
        if sb.getAttribute("bundleType")  == "BTLX":
            linuxbundlefound = True
            brands = sb.getElementsByTagName("Brand")
            brand_display = brands[0].getElementsByTagName("Display")
            models = sb.getElementsByTagName("Model")
            display = models[0].getElementsByTagName("Display")
            modelName = display[0].firstChild.data
            productName = (brand_display[0].firstChild.data + " " + display[0].firstChild.data)
            tempModelName = []
            for string in modelName.split():
                if any(char == '/' for char in string):
                    tempModelName.append(string.split('/', 1)[0])
                else:
                    tempModelName.append(string)
            modelName ="".join(tempModelName)
            acroymnList = re.findall('[A-Z][^A-Z]*', brands[0].getAttribute("prefix") + " " + modelName)
            temp_acroymn = []
            for acroymns in acroymnList:
                if any(char.isdigit() for char in acroymns):
                    temp_acroymn.append(acroymns.upper())
                else:
                    temp_acroymn.append(acroymns[0].upper())
            acroymnWithSpace = "".join(temp_acroymn)
            acroymn = "".join(acroymnWithSpace.split())
            listOfAvailablePlatforms[acroymn] = productName
    if not linuxbundlefound:
        dsulog("No linux Bundles available...",True)
        return ""
    if displayToConsole:
        print "List of available platforms..."
        maxLenOfModelNumber = max([len(k) for k in listOfAvailablePlatforms.keys()])
        ind = 1
        product_group_old=""
        for model, productName in sorted(listOfAvailablePlatforms.iteritems()):
            product_name = productName
            if ((ind -1) % 15 == 0 and ind!= 1 ):
                print '\x1b[1A' + '\x1b[1A'
            if (productName.split()[0].upper() != product_group_old.upper()):
                print '------------------------------------------'
                print '\t' + productName.split()[0]
                print '------------------------------------------'
                print '{index:1} {model:{model_len:d}s} {productName:3s}'.format(index="Index  ",
                                                                                 model_len=maxLenOfModelNumber + 6,
                                                                                 model="Model",
                                                                                 productName="Product Name")
            product_group_old = productName.split()[0]
            print '{index:1} {model:{model_len:d}s} {productName:3s}'.format(index=str(ind),
                                                                                 model_len=maxLenOfModelNumber + 7,
                                                                                 model='\t' + model,
                                                                                 productName=product_name)
            if (ind % 15 == 0):
                print("More... Press any key to continue")
                getch = GetchUnix()
                getch()
                CURSOR_UP_ONE = '\x1b[1A'
                ERASE_LINE = '\x1b[2K'
                print(CURSOR_UP_ONE + ERASE_LINE)
            ind = ind + 1
    return listOfAvailablePlatforms


def validate(xmlparser, xmlfilename):
    try:
        with open(xmlfilename, 'r') as f:
            etree.fromstring(f.read(), xmlparser)
        return True
    except etree.XMLSyntaxError as e:
        dsulog("XMLSyntaxError: " + str(e),True)
        return False
    except etree.XMLSchemaError:
        return False



def saveCustomCatalogAndValidate(doc):
    try:
        global disablePrintToConsole
        customCatalogPath = os.path.join(tempdir ,"Custom_Catalog.xml")
        f = open(customCatalogPath, "w")
        f.write(doc.toxml('UTF-16'))
        f.close()

        dsulog("Custom Catalog file created successfully...",False)

        if foundlxmlmodule:
            disablePrintToConsole= True
            xsdFilesFound= False
            totalxsdFiles = 0
            downloadSuccess = False
            xsdFiles=['Manifest.xsd','Bundle.xsd','DataModelCore.xsd','DriverPackManifest.xsd','Inventory.xsd','ManifestIndex.xsd','Package.xsd']
            protocols = ["https://", "http://"]
            urlLinks = ["downloads.dell.com", "ftp.dell.com"]
            xsdURLPath = '/Catalog/schema/2.7/'
            mininumSpaceRequiredByXSDFiles = 1000 # in KB
            xsdFilesDir = ""
            retrying = 0

            tree = etree.parse(customCatalogPath)
            root = tree.getroot()
            for rank in root.iter('Manifest'):
                rank.set('xmlns', 'openmanage/cm/dm')
            tree.write(os.path.join(tempdir ,"Catalog_schema.xml"))
            dsulog("Catalog schema file: "+ os.path.join(tempdir ,"Catalog_schema.xml"),False)
            if option.sourcelocation is not None:
                if isValidPath(option.sourcelocation,True):
                    pathOfXSD=executing_dir
                for item in range(0, len(xsdFiles)):
                    if isValidPath(os.path.join(pathOfXSD,xsdFiles[item]),True):
                        totalxsdFiles = totalxsdFiles + 1
            if totalxsdFiles == len(xsdFiles):
                xsdFilesFound = True
                xsdFilesDir = pathOfXSD

            if not xsdFilesFound:
                if isdiskFull(tempdir,mininumSpaceRequiredByXSDFiles):
                    dsulog("No space available for downloading XSD files. Hence, Skipping validation...",False)
                    disablePrintToConsole = False
                    return True

                for item in range(0, len(xsdFiles)):
                    if retrying != 0 and not downloadSuccess:
                        break
                    downloadSuccess = False
                    retrying = 0
                    xsdFilesDir = tempdir
                    for urlLink in urlLinks:
                        for protocol in protocols:
                            if downloadFile(protocol + urlLink + xsdURLPath + xsdFiles[item],os.path.join(tempdir,xsdFiles[item]),True):
                                downloadSuccess = True
                                break
                            retrying = retrying +1
                        if downloadSuccess:
                            break

            if downloadSuccess or xsdFilesFound:
                dsulog("XSD file directory: " + xsdFilesDir,False)
                os.chdir(xsdFilesDir)
                with open('Manifest.xsd', 'r') as f:
                    schema_root = etree.XML(f.read())
                schema = etree.XMLSchema(schema_root)
                xmlparser = etree.XMLParser(schema=schema,recover=True)
                os.chdir(executingDir)
                if validate(xmlparser, os.path.join(xsdFilesDir ,"Catalog_schema.xml")):
                    dsulog("XML File validated successfully...",False)
                else:
                    dsulog("XML File validation failed...",False)
                disablePrintToConsole = False
                return True
            else:
                dsulog("xsd files download failed. Hence skipping schema validation...",False)
            disablePrintToConsole = False
        else:
            dsulog("lxml module not present skipping validation...",False)

        return True
    except:
        e = sys.exc_info()
        dsulog("Validation Failed", False)
        dsulog("Exception: " + str(e), False)
        disablePrintToConsole = False
        os.chdir(executingDir)
        pass
        return True


def addSoftwareBundle(sb,applicablePlatforms):
    if sb.getAttribute("bundleType")  != "BTLX":
        return False
    brands = sb.getElementsByTagName("Brand")
    brand_display = brands[0].getElementsByTagName("Display")
    models = sb.getElementsByTagName("Model")
    display = models[0].getElementsByTagName("Display")
    productName= (brand_display[0].firstChild.data  + " " + display[0].firstChild.data)
    if productName.upper() in applicablePlatforms.values():
        return True
    return False


def addSoftwareComponent(sc,applicablePlatforms):
    if sc.getAttribute("packageType") != "LLXP":
        return ""
    brands = sc.getElementsByTagName("Brand")
    for brand in brands:
        found = False
        brand_display = brand.getElementsByTagName("Display")
        models = brand.getElementsByTagName("Model")
        for model in models:
            display = model.getElementsByTagName("Display")
            productName= (brand_display[0].firstChild.data  + " " + display[0].firstChild.data)
            if productName.upper() in applicablePlatforms.values():
                found = True
            else:
                model.parentNode.removeChild(model)
        if not found:
            brand.parentNode.removeChild(brand)

    if len(sc.getElementsByTagName("Brand")):
        return sc
    else:
        return ""
    return ""

def createCustomCatalog(xdCatalog,applicablePlatforms):
    doc = minidom.Document()
    root = doc.createElement('Manifest')

    for attribute in xdCatalog.documentElement.attributes.items():
        root.setAttribute(attribute[0],attribute[1])

    releaseNotes = xdCatalog.getElementsByTagName("ReleaseNotes")
    for releaseNote in releaseNotes:
        root.appendChild(releaseNote)

    inventoryComponents = xdCatalog.getElementsByTagName("InventoryComponent")
    for inventoryComponent in inventoryComponents:
        if inventoryComponent.getAttribute("osCode") =="LIN64":
            root.appendChild(inventoryComponent)

    softwareBundles = xdCatalog.getElementsByTagName("SoftwareBundle")
    for softwareBundle in softwareBundles:
        if addSoftwareBundle(softwareBundle,applicablePlatforms):
            root.appendChild(softwareBundle)

    softwareComponents = xdCatalog.documentElement.getElementsByTagName("SoftwareComponent")
    for softwareComponent in softwareComponents:
        sc = addSoftwareComponent(softwareComponent,applicablePlatforms)
        if sc:
            root.appendChild(sc)

    prerequistes = xdCatalog.getElementsByTagName("Prerequisites")
    for prerequiste in prerequistes:
        root.appendChild(prerequiste)


    doc.appendChild(root)
    if saveCustomCatalogAndValidate(doc):
        return True
    else:
        return False

def inputPlatfromList(inputPlatformlist,catalogFile):
    listOfAvailablePlatforms=displayPlatformInfo(catalogFile,False)
    if not listOfAvailablePlatforms:
        return -1
    platformDict = defaultdict(dict)
    platformList=[]
    if '|' in inputPlatformlist and ',' in inputPlatformlist:
        dsulog("list of platforms should be either pipe or comma separated ",True)
        return -1
    elif ',' in inputPlatformlist:
        platformList = inputPlatformlist.split(",")
    elif '|' in inputPlatformlist:
        platformList = inputPlatformlist.split("|")
    else:
        platformList.insert(1,inputPlatformlist)

    platformList = [platform.strip(' ') for platform in platformList]
    platformList = filter(None,platformList) # Filtering out None form list
    invalidPlatform=[platform for platform in platformList if platform.upper() not in listOfAvailablePlatforms.keys()]
    if invalidPlatform:
        dsulog("Invalid Platform Value(s) found : "+ ','.join(set(invalidPlatform)),True)
        return -1
    else:
        for platform in  platformList:
            if platform.upper() in listOfAvailablePlatforms.keys():
                platformDict[platform.upper()]= listOfAvailablePlatforms[platform.upper()].upper()
        dsulog("Creating Custom Catalog...",False)
        if createCustomCatalog(catalogFile,platformDict):
            return 0
        else:
            return -1
    return 0

def isUrl(filelinkToDownload):
    try:
        dsulog("Checking URL Path " + filelinkToDownload, False)
        ret = urllib2.urlopen(filelinkToDownload)
    except:
        return False
    return True


def isValidPath(path, isFilePath):
    dsulog("Checking Local Path " + path, False)
    if isFilePath:
        if os.path.isfile(path):
            dsulog(path + " Exists", False)
            return True
        else:
            return False
    else:
        if os.path.isdir(path):
            dsulog(path + " Exists", False)
            return True
        else:
            return False
    return True


def downloadFile(filelinkToDownload, filepathToSave, deleteIfPresent):
    if isValidPath(filepathToSave, True):
        filePresent = True
    else:
        filePresent = False
    if deleteIfPresent:
        if filePresent:
            dsulog("Deleting: " + filepathToSave, False)
            dsulog(">>>>>>>>>>>>>>>>>>>>>> rm log start", False)
            ret = os.system("rm -f " +  "\""  +filepathToSave +  "\"" )
            dsulog("<<<<<<<<<<<<<<<<<<<<<< rm log end", False)
            dsulog("ret=" + str(ret), False)
    try:
        dsulog("Downloading: " + filelinkToDownload, False)
        resp = urllib2.urlopen(filelinkToDownload)
        with open(filepathToSave, 'wb') as output:
            while True:
                data = resp.read(4096)
                if data:
                    output.write(data)
                else:
                    break
        st = os.stat(filepathToSave)
        os.chmod(filepathToSave, st.st_mode | stat.S_IEXEC)  # stat.S_IXOTH S_IXUSR
    except:
        e = sys.exc_info()
        dsulog("Download Failed. Please check the logs", True)
        dsulog("Exception: " + str(e) + "\n", False)
        return False
    return True;


def validatePathAndDownload(inputFilePath, filepathToSave, isFilepath, deleteIfPresent):

    if isValidPath(inputFilePath, isFilepath):
        return os.path.abspath(inputFilePath)

    catalogList = ["Catalog.xml","Catalog.gz"]

    if isValidPath(inputFilePath, False):
        dsulog("Searching for catalog.xml/catalog.gz at the given location: " + inputFilePath, False)
        for catalogName in catalogList:
            if isValidPath(os.path.abspath(os.path.join(inputFilePath,catalogName)), isFilepath):
                dsulog("Catalog file path: " + os.path.abspath(os.path.join(inputFilePath,catalogName)), True)
                return os.path.abspath(os.path.join(inputFilePath,catalogName))

    elif isUrl(inputFilePath):
        inFilePath = inputFilePath
        filePath = filepathToSave
        if ( inputFilePath.find("Catalog.gz") == -1  and inputFilePath.find("Catalog.xml") == -1 ):
            validUrl = False
            for catalogName in catalogList:
                dsulog("Adding "+ catalogName  + " to url: " + inputFilePath, False)
                if inputFilePath[-1] != '/':
                    inFilePath = inputFilePath + "/" + catalogName
                else:
                    inFilePath = inputFilePath + catalogName
                filePath = os.path.join(filepathToSave,catalogName)
                if isUrl(inFilePath):
                    validUrl = True
                    break
            if not validUrl:
                return ""
        else:
            filePath = os.path.join(filepathToSave,inputFilePath.rsplit('/', 1)[-1])

        dsulog("Downloading: " + inFilePath, True)
        if isdiskFull(os.path.dirname(filePath),mininumSpaceRequiredByCatalog):
            return "diskFull"
        if not downloadFile(inFilePath, filePath, deleteIfPresent):
            return ""
        else:
            return os.path.abspath(filePath)

    return ""


def downloadDUP(repositoryRoot, sc, base_url, deleteIfPresent):
    try:
        pathAttr = sc.getAttribute("path")
        filepathToSave = os.path.join(repositoryRoot, pathAttr)
        if os.path.isfile(filepathToSave):
            if deleteIfPresent:
                dsulog("Deleting: " + pathAttr, False)
                dsulog(">>>>>>>>>>>>>>>>>>>>>> rm log start", False)
                ret = os.system("rm -f " +  "\"" + filepathToSave +  "\"")
                dsulog("<<<<<<<<<<<<<<<<<<<<<< rm log end", False)
                dsulog("ret=" + str(ret), False)
            else:
                dsulog("Already present: " + pathAttr, True)
                st = os.stat(filepathToSave)
                os.chmod(filepathToSave, st.st_mode | stat.S_IEXEC)  # stat.S_IXOTH S_IXUSR
                return 0
    except:
        e = sys.exc_info()
        dsulog("Error occurred. Check the logs", True)
        dsulog("Exception: " + str(e) + "\n", False)
        return -1

    filelinkToDownload = os.path.join(base_url, pathAttr)
    destination_dir = os.path.dirname(filepathToSave)
    if destination_dir:
        mkdir_p(destination_dir)
    dsulog("Downloading: " + filelinkToDownload, False)

    try:
        resp = urllib2.urlopen(filelinkToDownload)
        with open(filepathToSave, 'wb') as output:
            while True:
                data = resp.read(4096)
                if data:
                    output.write(data)
                else:
                    break

        st = os.stat(filepathToSave)
        os.chmod(filepathToSave, st.st_mode | stat.S_IEXEC)  # stat.S_IXOTH S_IXUSR
    except:
        e = sys.exc_info()
        dsulog("Download Failed. Please check the logs", True)
        dsulog("Exception: " + str(e) + "\n", False)
        return -1

    return 0;


def downloadDUPAndVerify(repositoryRoot, sc, base_url):
    try:
        i = 0
        flag = 0
        pathAttr = sc.getAttribute("path")
        filepath = os.path.join(repositoryRoot, pathAttr)
        if os.path.isfile(filepath) and verifyFile(repositoryRoot, sc) != 0:
            deleteIfPresent = True
        else:
            deleteIfPresent = False
        if sc.nodeName == "SoftwareComponent":
            if sc.getAttribute("size") != "":
                scSize = int(sc.getAttribute("size")) / 1024 + 50 # Converting to KB
            else:
                scSize = 0
        else:
            scSize = 80000 # Estimated IC size in KB
        if isdiskFull(repositoryRoot,scSize):
            dsulog("No space available for downloading dups...",True)
            return 1

        dsulog("Downloading: " + pathAttr.rsplit('/', 1)[-1], True)

        if not base_url:
            urlLinks = ["downloads.dell.com","ftp.dell.com"]
            protocols = ["https://","http://","ftp://"]
        else:
            if isUrl(base_url):
                protocols = [base_url.split(':',1)[0] + '://']
                urlLinks = [base_url.split('//',1)[-1]]
            else:
                urlLinks = [base_url]
                protocols = ["https://","http://","ftp://"]

        for urlLink in urlLinks:
            for protocol in protocols:
                base_url = os.path.join(protocol , urlLink)
                if not i == 0:
                    deleteIfPresent = True
                    dsulog("Deleting", False)
                    dsulog("Retrying using " + base_url, True)
                else:
                    dsulog("Trying to connect using " + base_url, False)
                if downloadDUP(repositoryRoot, sc, base_url, deleteIfPresent) == 0:
                    dsulog("Verifying", False)
                    if verifyFile(repositoryRoot, sc) == 0:
                        flag =1
                        dsulog("Successfully downloaded.", True)
                        return 0
                i = i +1

        if flag == 1:
            return 0
        else:
            return -1
    except:
        e = sys.exc_info()
        dsulog("Exception: " + str(e) + "\n", False)
        return -1


def copyfileToRepo(sc,repositoryRoot,baseLocation):
    try:

        baseLocation = os.path.abspath(baseLocation)
        dupFile= sc.getAttribute("path")
        dupFileDir = os.path.dirname(dupFile)
        dupFileSize = sc.getAttribute("size")
        if sc.nodeName == "SoftwareComponent":
            if dupFileSize != "":
                dupFileSize  = int(dupFileSize) / 1024 + 50 # Converting to KB
            else:
                dupFileSize = 0
        else:
            dupFileSize = 8000 #Estimated size of IC in KB
        repodupDir = os.path.join(repositoryRoot, dupFileDir)
        if not mkdir_p(repodupDir):
            dsulog(repodupDir +" Creation Failed.",True)
            return False
        if isdiskFull(repodupDir,dupFileSize): # Converting dupsize to KB
            dsulog("No space available at: " + repodupDir+ " Please check logs for more details.",True)
            return False
        dsulog("Copying "+ os.path.join(baseLocation,dupFile) + " to "+ os.path.join(repositoryRoot,sc.getAttribute("path")), False)
        shutil.copy2(os.path.join(baseLocation,dupFile),os.path.join(repositoryRoot,sc.getAttribute("path")))
        st = os.stat(os.path.join(repositoryRoot,sc.getAttribute("path")))
        os.chmod(os.path.join(repositoryRoot,sc.getAttribute("path")), st.st_mode | stat.S_IEXEC)  # stat.S_IXOTH S_IXUSR
        return True
    except:
        e = sys.exc_info()
        dsulog("Exception: " + str(e) + "\n", True)
        return False


def verifyRepository(repositoryRoot,baseLocation):
    userOption = ""
    baseLocation=os.path.abspath(baseLocation)
    dsulog("Verifying Repository: " + baseLocation, True)
    dsulog("Reading Catalog file: Catalog.xml", False)
    handle = minidom.parse(os.path.join(repositoryRoot, "Catalog.xml"))

    dsulog("Iterating inventory components ...", True)
    inventoryComponentsNodeList = handle.getElementsByTagName("InventoryComponent")
    totalCount = 0
    for ic in inventoryComponentsNodeList:
        if ic.getAttribute("osCode") == "LIN64":
            totalCount += 1
    dsulog("Total:" + str(totalCount), True)
    total = 0
    missingCount = 0
    hashmismatch = 0
    for ic in inventoryComponentsNodeList:
        if ic.getAttribute("osCode") != "LIN64":
            continue
        ret = verifyFile(baseLocation, ic)
        if ret == -1:
            missingCount += 1
            dsulog("Inventory component missing: "+ os.path.join(baseLocation,ic.getAttribute("path")), True)
            return -1
        elif ret == -2:
            hashmismatch += 1
            dsulog("Inventory component hashmismatch: "+ os.path.join(baseLocation,ic.getAttribute("path")), True)
            return -1
        else:
            if not copyfileToRepo(ic,repositoryRoot,baseLocation):
                return -1

    dsulog("Iterating packages ...", True)
    softwareComponentsNodeList = handle.getElementsByTagName("SoftwareComponent")
    totalCount = 0
    for sc in softwareComponentsNodeList:
        if sc.getAttribute("packageType") == "LLXP":
            totalCount += 1

    dsulog("Total:" + str(totalCount), True)
    total = 0
    missingCount = 0
    hashmismatch = 0
    for sc in softwareComponentsNodeList:
        if sc.getAttribute("packageType") != "LLXP":
            continue
        ret = verifyFile(baseLocation, sc)
        if ret == -1:
            missingCount += 1
            dsulog("Software component missing: "+ os.path.join(baseLocation,sc.getAttribute("path")), True)
        elif ret == -2:
            hashmismatch += 1
            dsulog("Software component hashmismatch: "+ os.path.join(baseLocation,sc.getAttribute("path")), True)
        else:     # copying the respective file to repository location
            if not copyfileToRepo(sc,repositoryRoot,baseLocation):
                return -1
    dsulog(str(missingCount) + " files missing out of total " + str(totalCount) + "\n", False)
    dsulog(str(hashmismatch) + " hash mismatch out of total " + str(totalCount), False)
    if missingCount > 0 or hashmismatch > 0:
        dsulog("Missing files:" + str(missingCount), True)
        dsulog("Hash mismatches:" + str(hashmismatch), True)
        invalidAnswer=0
        while (userOption.upper() != "YES" and userOption.upper() != "NO"):
            if invalidAnswer == 0:
                userOption = raw_input("Repository verification failed. Do you still want to continue? [NOTE: 'no' will clean the downloaded files at: "+ repositoryRoot + "] [yes/no]")
                invalidAnswer = invalidAnswer + 1
            else:
                userOption = raw_input("Invalid input: '" + userOption  + "' Repository verification failed. Do you still want to continue? [NOTE: 'no' will clean the downloaded files at: "+ repositoryRoot + "] [yes/no]")
            userOption = userOption.strip(' ')
            if userOption.upper() == "NO":
                return -1
        return 0

    dsulog("Verifying Repository Success", True)
    return 0


def fixRepository(repositoryRoot, base_url):
    dsulog("Fixing Repository: " + repositoryRoot, True)
    dsulog("Reading Catalog file: Catalog.xml", True)
    handle = minidom.parse(os.path.join(repositoryRoot, "Catalog.xml"))

    dsulog("Iterating packages ...", True)
    softwareComponentsNodeList = handle.getElementsByTagName("SoftwareComponent") + handle.getElementsByTagName(
        "InventoryComponent")
    totalCount = len(softwareComponentsNodeList)
    dsulog("Total:" + str(totalCount), True)

    total = 0
    fixFailed = 0
    for sc in softwareComponentsNodeList:
        ret = downloadDUPAndVerify(repositoryRoot, sc, base_url)
        if not ret == 0:
            fixFailed += 1
    if fixFailed > 0:
        dsulog("Fix Failed for packages:" + str(fixFailed), True)
        dsulog("Repository Fix failed. Check the log file for details.", True)
        return -1

    dsulog("Repository Fix Succeded", True)
    return 0


def createRepository(catalog, repositoryRoot, base_url):
    i =0
    userOption = ""

    dsulog("Getting components from catalog...", True)
    handle = minidom.parse(catalog)

    dsulog("Creating directory if not present: " + repositoryRoot, False)
    mkdir_p(repositoryRoot)

    dsulog("Copying " + os.path.abspath(catalog) + " to " + repositoryRoot + "/Catalog.xml", False)
    shutil.copy2(os.path.abspath(catalog), repositoryRoot + "/Catalog.xml")
    # fig.savefig(os.path.join(repositoryRoot, "Catalog.xml"))

    dsulog("Iterating inventoryComponents ...", True)
    inventoryComponentsNodeList  = handle.getElementsByTagName("InventoryComponent")
    totalCount = 0
    for ic in inventoryComponentsNodeList:
        if ic.getAttribute("osCode") == "LIN64":
            totalCount += 1

    dsulog("Total:" + str(totalCount), True)
    for ic in inventoryComponentsNodeList:
        if ic.getAttribute("osCode") != "LIN64":
            continue
        i += 1
        dsulog(str(i) + "/" + str(totalCount), True)
        ret = downloadDUPAndVerify(repositoryRoot, ic, base_url)
        if not ret == 0:
            dsulog("Inventory Component download failed hence exiting...", False)
            return -1

    dsulog("Iterating packages ...", True)
    i = 0
    softwareComponentsNodeList = handle.getElementsByTagName("SoftwareComponent")
    totalCount = 0
    for sc in softwareComponentsNodeList:
        if sc.getAttribute("packageType") == "LLXP":
            totalCount += 1

    dsulog("Total:" + str(totalCount), True)

    for sc in softwareComponentsNodeList:
        if sc.getAttribute("packageType") != "LLXP":
            continue
        i += 1
        dsulog(str(i) + "/" + str(totalCount), True)
        ret = downloadDUPAndVerify(repositoryRoot, sc, base_url)
        if ret == -1:
            invalidAnswer=0
            while (userOption.upper() != "YESTOALL" and userOption.upper() != "NO"):
                if invalidAnswer == 0:
                    userOption = raw_input("Repository verification failed. Do you still want to continue? [NOTE: 'no' will clean the downloaded files at: "+ repositoryRoot + "] [yestoall/no]")
                    invalidAnswer = invalidAnswer + 1
                else:
                    userOption = raw_input("Invalid input: '" + userOption  + "' Repository verification failed. Do you still want to continue? [NOTE: 'no' will clean the downloaded files at: "+ repositoryRoot  +  "] [yestoall/no]")
                userOption = userOption.strip(' ')
                if userOption.upper() == "NO":
                    return -1
        elif ret == 1:
            return -1


    dsulog("Repository Created at " + repositoryRoot, False)
    return 0


def createBootScript(filepath):
    script = open(filepath, "w")
    script.write("#!/bin/bash\n")
    script.write("set -e\n")
    script.write("shopt -s expand_aliases\n")
    script.write("alias 'rpm=rpm --ignoresize'\n")
    script.write("mkdir -p /var/cache/yum\n")
    script.write("mount -ttmpfs tmpfs /var/cache/yum\n")
    script.write("rpm -ivh --nodeps /opt/dell/toolkit/systems/RPMs/rhel7/yumrpms/*\n")
    script.write("echo \"diskspacecheck=0\" >> /etc/yum.conf\n")
    script.write("echo \"Installing dell-system-update ...\"\n")
    script.write("if rpm -U --force /opt/dell/toolkit/systems/RPMs/dell-system-update*.rpm\n")
    script.write("then\n")
    script.write("  echo \"DSU installation successful ...\"\n")
    script.write("  export LANG=en_US.UTF-8\n")
    script.write( "else\n")
    script.write("  echo \"DSU installation failed.\"\n")
    script.write("  exit 1\n")
    script.write("fi\n")
    script.write("mkdir -p /usr/libexec/dell_dup/\n")
    if option.applyaction is None:
        script.write("echo \"Starting dsu ...\"\n")
        script.write("dsu --non-interactive --source-type=REPOSITORY --source-location=/opt/dell/toolkit/systems/repository/\n")
    if applyactionApplyall:
        script.write("echo \"Starting dsu ...\"\n")
        script.write("dsu --non-interactive --apply-equivalent-updates --source-type=REPOSITORY --source-location=/opt/dell/toolkit/systems/repository/\n")
    if applyactionEquivalent:
        script.write("echo \"Starting dsu to apply only equivalents...\"\n")
        script.write("dsu --non-interactive --apply-equivalent-updates --source-type=REPOSITORY --source-location=/opt/dell/toolkit/systems/repository/\n")
    if applyactionUpgrade:
        script.write("echo \"Starting dsu to apply only Upgrades ...\"\n")
        script.write("dsu --non-interactive  --apply-upgrades-only --source-type=REPOSITORY --source-location=/opt/dell/toolkit/systems/repository/\n")
    if applyactionDowngrade:
        script.write("echo \"Starting dsu to apply only Downgrades ...\"\n")
        script.write("dsu --non-interactive --apply-downgrades-only --source-type=REPOSITORY --source-location=/opt/dell/toolkit/systems/repository/\n")
    script.close()

    os.chmod(filepath, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
    return 0


def createBootableDSU(repositoryRoot, isofile, inputScriptFile):
    try:
        os.chdir(tempdir)
        bootpluginRootDir = os.path.abspath(bootpluginExtractDir)
        bootpluginRepoDir = os.path.join(bootpluginRootDir, "repository")
        bootpluginScriptFile = os.path.join(bootpluginRootDir, "drm_files/apply_bundles.sh")

        dsulog("Transferring required files.", False)

        if inputScriptFile is not  None:
            dsulog("Copying "+ inputScriptFile+" to "+ bootpluginScriptFile, True)
            shutil.copy2(inputScriptFile,bootpluginScriptFile)
            os.chmod(bootpluginScriptFile, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        else:
            dsulog("Creating script file: " + bootpluginScriptFile, False)
            createBootScript(bootpluginScriptFile);

        dsulog("Moving repository - " + repositoryRoot + " to " + bootpluginRepoDir, False)
        shutil.move(repositoryRoot, bootpluginRepoDir)
        # shutil.copytree(repositoryRoot, bootpluginRepoDir)

        dsulog("Creating ISO", True)

        createiso_command = "mkisofs -joliet-long -o '{0}' -b isolinux/isolinux.bin -c isolinux/boot.catalog -no-emul-boot -boot-load-size 4 -boot-info-table -pad -r -J -hide-joliet-trans-tbl -eltorito-alt-boot -eltorito-boot efiboot.img -no-emul-boot '{1}' 1>>'{2}' 2>>'{2}'".format(
            isofile, bootpluginRootDir, logfilePath)

        dsulog(createiso_command, False)
        dsulog(">>>>>>>>>>>>>>>>>>>>>> mkisofs log start", False)
        ret = os.system(createiso_command)
        dsulog("<<<<<<<<<<<<<<<<<<<<<< mkisofs log end", False)
        if not ret == 0:
            dsulog("ISO creation failed", True)
            dsulog("command ret value:" + str(ret), False)
            dsulog("Moving back repository - from " + bootpluginRepoDir + " to " + repositoryRoot, False)
            shutil.move(bootpluginRepoDir, repositoryRoot)
            os.chdir(executingDir)
            return -1
        else:
            dsulog("ISO file created: " + isofile, True)
    finally:
        os.chdir(executingDir)
    return 0


def getdellbootpluginFile(inputFilePath,filepathToSave):
    dellbootpluginPath=""
    if isValidPath(inputFilePath,True):
        dellbootpluginPath =  os.path.abspath(inputFilePath)

    elif isUrl(inputFilePath):
        dsulog("Downloading: " + inputFilePath, True)
        filePath = os.path.join(filepathToSave,inputFilePath.rsplit('/', 1)[-1])
        if isdiskFull(os.path.dirname(filePath),mininumSpaceRequiredByDTK):
            return "diskFull"
        if not downloadFile(inputFilePath, filePath, True):
            return ""
        else:
            dellbootpluginPath =os.path.abspath(filePath)

    if dellbootpluginPath == "":
        dsulog("Invalid dellbootplugin location: "+ inputFilePath,True)
        return ""
    else:
        dsulog("Extracting dellbootplugin: " + os.path.basename(dellbootpluginPath), True)
        if not extractTARGZ(dellbootpluginPath):
            dsulog("Extraction failed. Supported format is tar.gz",True)
            return ""

    return dellbootpluginPath


def parseDSUPLugin(inputFilePath,dellbootpluginLocation):
    dsulog("Parsing "+ inputFilePath, False)
    try:
        dsupluginFile = minidom.parse(inputFilePath)
        rmplugins = dsupluginFile.getElementsByTagName("RMPlugins")
        pluginBaselocation = rmplugins[0].getAttribute("baselocation")
        if not pluginBaselocation:
            dsulog("Parsing DSUPlugin.xml failed...",True)
            return False
        dsulog("baselocation in DSUPLugin.xml: "+ pluginBaselocation, False)
        child = rmplugins[0].firstChild
        while child != None:
            if child.nodeType == minidom.Node.ELEMENT_NODE and child.getAttribute("type") == "DDM":
                fileName=child.getElementsByTagName("FileName")
                dsulog("PluginLocation: " + fileName[0].childNodes[0].data, False)
                dellbootpluginLocation.append(pluginBaselocation +"/" + fileName[0].childNodes[0].data)
                dsulog("PluginLocation: " + pluginBaselocation +"/" + fileName[0].childNodes[0].data, False)
                break
            child = child.nextSibling
        return True
    except:
        e = sys.exc_info()
        dsulog("Parsing DSUPlugin.xml failed...",True)
        dsulog("Exception: " + str(e) + "\n", False)
        return False

def getCatalogFile(cataloglocation):
    catalogFilePath = validatePathAndDownload(cataloglocation, tempdir, True,
                                              True)
    if catalogFilePath == "diskFull":
        return "diskFull"
    elif catalogFilePath:
        dsulog("Catalog file absolute path  " + catalogFilePath, False)
        fileExtension = getFileExtension(catalogFilePath)
        dsulog("Extension of the File " + catalogFilePath + " - " + fileExtension, False)
        if fileExtension.upper() == ".GZ":
            if extractGZ(catalogFilePath, os.path.join(tempdir, "Catalog.xml"), True):
                catalogFilePath = os.path.join(tempdir , "Catalog.xml")
            else:
                return ""
        elif fileExtension.upper() != ".XML":
            dsulog(catalogFilePath + " - unknown/unsupported Catalog file extention. Supported are xml, gz.", True)
            return ""
        return catalogFilePath
    else:
        dsulog("Catalog File not present or invalid: " + cataloglocation, True)
        return ""


def verifyAndCreatePath(inPath):
    if not inPath:
        dsulog("Location can not be empty", True)
        return False

    if inPath[-1] == '/':
        inPath = inPath[:-1]

    if inPath !=  os.path.normpath(inPath):
        dsulog("Location: "+ inPath + " is invalid.", True)
        dsulog("Retry with Location: "+ os.path.normpath(inPath), True)
        return False
    return True

def dsuinit():
    global logfilePath
    global workdir
    global logEnable

    if logfilePath is None:
        logfilePath = "/var/log"
        logfileName="dsucreateiso.log"
    else:
        logfileName="dsucreateiso_" +  datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".log"
    if verifyAndCreatePath(logfilePath):
        logPath = os.path.abspath(logfilePath)
        if isValidPath(logPath, True):
            dsulog("Invalid directory. Please provide a valid directory...", True)
            return False
        if isValidPath(logPath, False):
            if not os.access(logPath, os.W_OK | os.R_OK | os.X_OK):
                dsulog("Log Location is not writable:" + logPath, True)
                return False
        else:
            dsulog("Creating " + logPath, False)
            if not mkdir_p(logPath):
                return False
    else:
        return False
    logfilePath = os.path.join(logPath,logfileName)
    if isValidPath(logfilePath, True):
        if not os.access(logfilePath, os.W_OK | os.R_OK ):
            dsulog("Log File is not writable: "+ logfilePath, True)
            return False
    logEnable = True
    logformat = '%(levelname)s#%(asctime)s#%(message)s'
    logging.basicConfig(format=logformat, datefmt='%m/%d/%Y %I:%M:%S %p', filename=logfilePath, level=logging.INFO)
    dsulog("===========================================Create Bootable DSU======================================",
           False)
    dsulog("Timestamp:" + str(datetime.datetime.utcnow()), False)

    if not (workdir is None):
        if verifyAndCreatePath(workdir):
            workdir = os.path.abspath(workdir)
            if isValidPath(workdir, True):
                dsulog("Invalid directory. Please provide a valid directory...", True)
                return False
            if isValidPath(workdir, False):
                if not os.access(workdir, os.W_OK | os.R_OK | os.X_OK):
                    dsulog("Workspace Location is not writable:" + workdir, True)
                    return False
            else:
                dsulog("Creating " + workdir, False)
                if not mkdir_p(workdir):
                    return False
        else:
            return False
        tempfile.tempdir = workdir

    return True



def isoptionsCombinedValid(option):
    isValid = True
    if option.displayPlatformlist is not None:
        invalidCombinations=[option.output,'--output' ,option.inputPlatformlist,'--input-platformlist', option.applyaction,'--applyaction',option.inputscript,'--input-custom-script',option.outputscript,'--output-custom-script',option.dellbootplugin,'--dellbootplugin']
        for i in xrange(0,len(invalidCombinations),2): # xrange is valid for python2 , It's range from python3
            if invalidCombinations[i] is not None:
                dsulog("Options --available-platforms and %s cannot be combined" % (invalidCombinations[i+1]), True)
                isValid = False

    if option.inputscript is not None:
        invalidCombinations=[option.applyaction,'--applyaction',option.outputscript,'--output-custom-script']
        for i in xrange(0,len(invalidCombinations),2): # xrange is valid for python2 , It's range from python3
            if invalidCombinations[i] is not None:
                dsulog("Options --input-custom-script and %s cannot be combined" % (invalidCombinations[i+1]), True)
                isValid = False

    if option.outputscript is not None:
        invalidCombinations=[option.output,'--output' ,option.sourcelocation,'--source-location',option.inputPlatformlist,'--input-platformlist',option.dellbootplugin,'--dellbootplugin']
        for i in xrange(0,len(invalidCombinations),2): # xrange is valid for python2 , It's range from python3
            if invalidCombinations[i] is not None:
                dsulog("Options --output-cucstom-script and %s cannot be combined" % (invalidCombinations[i+1]), True)
                isValid = False

    return isValid


def add_createbootabledsu_command_options(mainparser):
    # Creating subcommand 'createbootabledsu'
    opts_grp = OptionGroup(
        mainparser, 'Create Bootable DSU Options',
        'These options control the Bootable DSU creation.',
    )

    opts_grp.add_option('-o', '--output',
    help = "Destination path to save the ISO file created.")

    opts_grp.add_option('-p', '--available-platforms', action="store_true", dest="displayPlatformlist",
    help = "Displays the list of available platforms.")

    opts_grp.add_option('-i','--input-platformlist',action="store", type="string", dest="inputPlatformlist",
                help="Input list of Platforms separated with pipe or comma.")

    opts_grp.add_option('-s','--source-location', action="store", type="string", dest="sourcelocation",
    help = "Location of catalog file" )

    opts_grp.add_option('-l','--log-location', action="store", type="string", dest="loglocation",
    help = "Location of Log file" )

    opts_grp.add_option('-a','--apply-action', action="store", type="string", dest="applyaction",
    help = "Choose the action[applyall|upgrade|downgrade|equivalent] for the components." )

    opts_grp.add_option('-d', '--dellbootplugin', action="store", dest="dellbootplugin",
    help = "Location of dellbootplugin in tar.gz format.")

    opts_grp.add_option('-c', '--input-custom-script', action="store", dest="inputscript",
    help = "Location of custom script file used for ISO creation.")

    opts_grp.add_option('-u', '--output-custom-script', action="store", dest="outputscript",
    help = "Destination path to save custom script file used for ISO generation.")

    mainparser.add_option_group(opts_grp)


def main():
    global workdir
    global tempdir
    global executingDir
    global logEnable
    global logfilePath
    global disablePrintToConsole
    global mininumSpaceRequiredByCatalog
    global mininumSpaceRequiredByDTK
    global mininumSpaceRequiredByScript
    global option
    global bootpluginExtractDir
    global applyactionUpgrade
    global applyactionDowngrade
    global applyactionEquivalent
    global applyactionApplyall

    baseurl = ""
    mininumSpaceRequiredByCatalog = 50000 # in KB
    mininumSpaceRequiredByDTK = 3000000 # in KB
    mininumSpaceRequiredByScript = 10 # in KB
    applyActionList=["applyall", "upgrade", "downgrade","equivalent"]
    applyactionUpgrade = False
    applyactionDowngrade = False
    applyactionEquivalent = False
    applyactionApplyall = False

    repositoryPath = ""
    dellbootpluginSuccessfulVerfication = False
    systemCmd = "mkisofs --help 2>/dev/null"
    parser = OptionParser()
    parser.add_option('-w', '--workspace',
                      help="Workspace directory to be used by the script")
    add_createbootabledsu_command_options(parser)
    option, remainder = parser.parse_args()
    executingDir = os.getcwd()

    logEnable = False
    disablePrintToConsole= False
    logfilePath = option.loglocation
    workdir = option.workspace

    if remainder:
        dsulog("Usage: dsucreateiso [options]\n",True)
        dsulog("dsucreateiso: error: no such option: " + ''.join(remainder), True)
        return -1

    if not isoptionsCombinedValid(option):
        return -1

    if not dsuinit():
        return -1

    dsulog("Checking for mkisofs command.",False)
    if os.system(systemCmd):
        dsulog("mkisofs: command not found. Please install mkisofs to create bootable iso.",True)
        return -1

    dsulog("Input options: " + str(option), False)
    dsulog("Input remainder: " + str(remainder), False)
    dsulog("Log file:" + logfilePath, True)
    dsulog("executingDir:" + executingDir, False)

    with TemporaryDirectory() as temporaryDir:
        tempdir = temporaryDir
        dsulog("tempdir:" + tempdir, False)
        try:

            repositoryPath = os.path.join(tempdir,"repo")
            dsulog("Repository Path: " + repositoryPath, False)
            if not os.access(tempdir, os.W_OK | os.R_OK |os.X_OK ):
                dsulog("Directory:" + os.path.abspath(tempdir) + " is not writable", True)
                return -1

            bootpluginExtractDir = os.path.join(tempdir,"dellbootplugin")

            if option.applyaction is not None:
                applyActions = []
                if '|' in option.applyaction and ',' in option.applyaction:
                    dsulog("list of actions should be either pipe or comma separated ",True)
                    return -1
                elif '|' in option.applyaction:
                    applyActions  = option.applyaction.split("|")
                elif ',' in option.applyaction:
                    applyActions = option.applyaction.split(",")
                else:
                    applyActions.insert(1,option.applyaction)
                applyActions = [applyAction.strip(' ') for applyAction in applyActions]
                applyActions = filter(None,applyActions) # Filtering out None form list
                invalidapplyAction=[applyAction for applyAction in applyActions if applyAction.lower() not in applyActionList]
                if invalidapplyAction:
                    dsulog("Invalid action Value(s) found : "+ ','.join(set(invalidapplyAction)),True)
                    return -1
                for applyAction in applyActions:
                    if applyAction.lower() == "upgrade":
                        applyactionUpgrade = True
                    elif applyAction.lower() == "equivalent":
                        applyactionEquivalent = True
                    elif  applyAction.lower() == "downgrade":

                        applyactionDowngrade = True
                    else:
                        applyactionApplyall = True
                if applyactionApplyall and (applyactionDowngrade or applyactionEquivalent or applyactionUpgrade):
                    dsulog("applyall can not be combined with other choices.", True)
                    return -1

            if option.inputscript is not None:
                option.inputscript = os.path.abspath(option.inputscript)
                if not option.inputscript:
                    dsulog("Input custom location can not be empty.", True)
                    return -1
                elif isValidPath(option.inputscript,False):
                    dsulog("Invalid File: " + option.inputscript, True)
                    return -1
                elif isUrl(option.inputscript):
                    if not isdiskFull(tempdir,100): # 100 is the minimum size required by any script file.
                        if downloadFile(option.inputscript,os.path.join(tempdir,"apply_bundles.sh"),True):
                            option.inputscript = os.path.join(tempdir,"apply_bundles.sh")
                        else:
                            return -1
                    else:
                        dsulog("No available space for downloading script file: "+ option.inputscript, True)
                        return -1
                elif not isValidPath(option.inputscript,True):
                    dsulog("Invalid Location: "+ option.inputscript, True)
                    return -1


            if option.outputscript is not None:
                if not option.outputscript:
                    dsulog("Output custom location can not be empty.", True)
                    return -1
                elif isValidPath(option.outputscript,True):
                    dsulog("File exist: "+ option.outputscript+ ". Please provide a valid location.", True)
                    return -1
                elif not isValidPath(option.outputscript,False):
                    dsulog("Location: "+ option.outputscript+ " does not exist.", True)
                    return -1
                elif not os.access(option.outputscript, os.W_OK | os.R_OK | os.X_OK):
                    dsulog("Location:" + os.path.abspath(option.outputscript) + " is not accessible", True)
                    return -1
                elif isdiskFull(option.outputscript,mininumSpaceRequiredByScript):
                    dsulog("No space avialbale at: "+ option.outputscript + ". Minimum required is "+ str(mininumSpaceRequiredByScript), True)
                    return -1
                else:
                    scriptPath = os.path.join(option.outputscript, "apply_bundles_"  + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".sh")
                    createBootScript(scriptPath)
                    dsulog("Path to script file: " + os.path.abspath(scriptPath), True)
                    return 0


            if option.output is None:
                option.output = "dsu_bootableimage_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".iso"
                if isValidPath(option.output,True):
                    dsulog("File already present: " + os.path.abspath(option.output) + " Please provide a different filename.", True)
                    return -1
                if not os.access(executingDir, os.W_OK | os.R_OK ):
                    dsulog("Location is not writable: " + os.path.abspath(executingDir), True)
                    return -1
                dsulog("ISO file output path - " + os.path.abspath(option.output), False)
            elif not option.output:
                dsulog("Output Location can not be empty.", True)
                return -1
            elif isValidPath(os.path.abspath(option.output), False):
                dsulog(
                    "File named " + os.path.abspath(option.output) + " is a directory. Please Provide a file name.",
                    True)
                return -1
            elif not isValidPath(os.path.dirname(os.path.abspath(option.output)), False):
                dsulog("Path " + os.path.dirname(
                    os.path.abspath(option.output)) + " does not exists. Please provide a valid location.", True)
                return -1
            elif isValidPath(option.output, True):
                dsulog(
                    "File named " + os.path.abspath(option.output) + " already present. Provide a different name.",
                    True)
                return -1
            elif not isWritable(os.path.abspath(option.output)):
                dsulog("Unable to write into " + os.path.abspath(option.output), True)
                return -1

            dellbootpluginPath = ""
            if option.dellbootplugin is None:
                if not option.displayPlatformlist:
                    protocols = ["ftp://","https://", "http://"]
                    urlLinks = ["ftp.dell.com","downloads.dell.com"]
                    retrying = 0
                    if not isdiskFull(tempdir,mininumSpaceRequiredByDTK):
                        for urlLink in urlLinks:
                            for protocol in protocols:
                                option.dellbootplugin = protocol + urlLink + "/sysman/DSUPlugins.tar"
                                if retrying != 0:
                                    dsulog("Retrying using " + protocol + urlLink , True)
                                else:
                                    dsulog("Downloading: " + option.dellbootplugin, True)
                                if downloadFile(option.dellbootplugin,os.path.join(tempdir,"DSUPlugins.tar"),True):
                                    dellbootpluginPath = os.path.join(tempdir,"DSUPlugins.tar")
                                    # Extracting tar to parse xml fiel to get location of dtk.tar.gz
                                    if not extractTARGZ(dellbootpluginPath):
                                        dsulog("Extraction failed.",True)
                                        return -1
                                    DSUPluginPath=os.path.join(tempdir,"DSUPlugins/DSUPlugins.xml")
                                    dsulog("DSUPluginPath: "+ DSUPluginPath, False)
                                    #Parse the file to get location of dtk plugin
                                    dellbootpluginLocation=[]
                                    if parseDSUPLugin(DSUPluginPath,dellbootpluginLocation):
                                        for proto in protocols:
                                            dellbootpluginPath = ""
                                            dellbootpluginPath =  getdellbootpluginFile(proto + dellbootpluginLocation[0].replace('\\', '/'),tempdir)
                                            if dellbootpluginPath:
                                                break
                                        if not dellbootpluginPath:
                                            return -1
                                    else:
                                        return -1
                                retrying = retrying + 1
                            if dellbootpluginPath:
                                break
                        if not dellbootpluginPath:
                            dsulog("Unable to download dellbootplugin. Please check the network connectivity...", True)
                            return -1
                    else:
                        dsulog("No space available for downloading dellbootplugin file...", True)
                        return -1
            elif not option.dellbootplugin:
                dsulog("dellbootplugin Location can not be empty.", True)
                return -1
            else:
                dellbootpluginPath  = getdellbootpluginFile(option.dellbootplugin,tempdir)
                if dellbootpluginPath == "diskFull":
                    dsulog("No space available for downloading dellbootplugin file...", True)
                    return -1
                elif not dellbootpluginPath:
                    return -1

            dsulog("dellbootpluginpath: " + dellbootpluginPath, False)
            dsulog("dellbootpluginextractedpath: " + bootpluginExtractDir, False)

            if not option.displayPlatformlist:
            # Verfying dellbootplugin
                for files in os.listdir(bootpluginExtractDir):
                    if files.endswith(".DRM") or files.endswith(".drm"):
                        dellbootpluginSuccessfulVerfication = True
                        break

                if not dellbootpluginSuccessfulVerfication:
                    dsulog("Invalid dellbootpluginpath: " + bootpluginExtractDir + ". *.DRM file missing", False)
                    dsulog("Invalid dellbootplugin.", True)
                    return -1

            catalogFilePath=""
            if option.sourcelocation is None:
                protocols = ["https://", "http://"]
                urlLinks = ["downloads.dell.com", "ftp.dell.com"]
                retrying = 0
                if not isdiskFull(tempdir,mininumSpaceRequiredByCatalog):
                    for urlLink in urlLinks:
                        for protocol in protocols:
                            option.sourcelocation = protocol + urlLink + "/catalog/Catalog.gz"
                            if retrying != 0:
                                dsulog("Retrying using " + protocol + urlLink , True)
                            else:
                                dsulog("Downloading: " + option.sourcelocation, True)
                            if downloadFile(option.sourcelocation,os.path.join(tempdir,"Catalog.gz"),True):
                                if extractGZ(os.path.join(tempdir,"Catalog.gz"), os.path.join(tempdir, "Catalog.xml"), True):
                                    catalogFilePath = os.path.join(tempdir, "Catalog.xml")
                                    break
                                else:
                                    dsulog("GZ Extraction Failed. Retrying", False)
                            retrying = retrying + 1
                        if catalogFilePath:
                            break
                    if not catalogFilePath:
                        dsulog("Unable to download Catalog. Please check the network connectivity...", True)
                        return -1
                else:
                    dsulog("No space available for downloading catalog file...", True)
                    return -1
            elif not option.sourcelocation:
                dsulog("Source Location can not be empty.", True)
                return -1
            else:
                catalogFilePath = getCatalogFile(option.sourcelocation)
                if not catalogFilePath:
                    return -1

            dsulog("Parsing Catalog File...", True)
            catalogFile = minidom.parse(catalogFilePath)

            if option.displayPlatformlist:
                displayPlatformInfo(catalogFile, True)
                return 0

            if option.inputPlatformlist:
                if inputPlatfromList(option.inputPlatformlist,catalogFile):
                    return -1
                else:
                    catalogFilePath = os.path.join(tempdir ,"Custom_Catalog.xml")

            dsulog("Parsing catalog file to get base location.",False)
            dsulog("Getting baseLocation from catalog...",True)
            catalogFile = minidom.parse(catalogFilePath)
            baseLocation  = catalogFile.documentElement.getAttribute("baseLocation")

            if isValidPath(option.sourcelocation,False): # In case PDK repositroy path given and baseLocation is empty
                baseLocation = option.sourcelocation

            if not mkdir_p(repositoryPath):
                dsulog("Repository directory creation failed: " + repositoryPath, True)
                return -1

            if not baseLocation or (not isValidPath(baseLocation,False) and not isValidPath(baseLocation,True)):
                if createRepository(catalogFilePath, repositoryPath, baseLocation) == 0:
                    dsulog("Repository created successfully...", False)
                else:
                    dsulog("Repository failed...", False)
                    dsulog("ISO creation Failed. Please check logs for more details...", True)
                    return -1
            else:
                if isValidPath(baseLocation,True):
                    dsulog("Invalid baseLocation found from catalog: "+ baseLocation, True)
                    return -1
                elif not isValidPath(baseLocation,False):
                    dsulog("baseLocation from catalog: "+ baseLocation + " does not exist.", True)
                    return -1
                dsulog("Copying "+catalogFilePath+" to "+ os.path.join(repositoryPath,"Catalog.xml"),False)
                shutil.copy2(catalogFilePath,os.path.join(repositoryPath,"Catalog.xml"))
                if verifyRepository(repositoryPath,baseLocation) == -1:
                    return -1


            ret = createBootableDSU(repositoryPath,os.path.abspath(option.output),option.inputscript)

        except:
            e = sys.exc_info()
            dsulog("Error occurred. Check the logs", True)
            dsulog("Exception: " + str(e), False)
            logging.info("Exception", exc_info=1)


if __name__ == "__main__":
    main()
    print "Exiting DSU ISO generator"
