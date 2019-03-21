#!/usr/local/bin/python

import os,sys
import xml.etree.ElementTree

tree = xml.etree.ElementTree.parse( sys.argv[1] )
server_model = sys.argv[2]
root = tree.getroot()
repository_path = ''
software = {}

for child in root.iter('SoftwareComponent'):
   path = child.attrib['path']
   basename = os.path.basename(path)

   if child.find('ComponentType').attrib['value'] not in ['FRMW','APAC']:
       continue
  
   software[basename]=[path]
   for subchild in child: 
       if subchild.tag == 'Name':
           software[basename].append((subchild.find('Display').text))
       elif subchild.tag == 'Description':
           software[basename].append((subchild.find('Display').text))
       elif subchild.tag == 'Category':
           software[basename].append((subchild.find('Display').text))
       elif subchild.tag == 'ImportantInfo':
           software[basename].append((subchild.attrib['URL']))
       elif subchild.tag == 'Criticality':
           software[basename].append((subchild.attrib['value']))


for child in root.iter('SoftwareBundle'):
   target = child.find('TargetSystems/Brand/Model/Display')
   if (target.text != server_model):
       continue
   if (child.attrib['bundleID'].find('WIN') == -1 ):
       continue

   print "## ---software bundle---"
   print "##", child.attrib['bundleID'], target.text
   print "## ---"

   contents = child.find('Contents')
   print "## The following packages are available:"

   for package in child.iter('Package'):
       mypath = package.attrib['path']
       if mypath in software.keys():
           print "File: {}\nName: {}\nDescription: {}\nCategory: {}\nInfoURL: {}\nCriticality: {}".format(software[mypath][0],software[mypath][1],software[mypath][2],software[mypath][3],software[mypath][4],software[mypath][5])
           print "---"

   print "## ---end of software bundle"
   print
