#!/usr/bin/env python3

import sys
import os
import mod_globals
import zipfile
import pickle
import shutil

errone   = {}
acfFile  = ""
zip      = None
zipflist = []

class ACE():
  VEH = ""
  REF = ""
  UCE = ""
  NOM = ""
  cfg = []
  dat = {}
  req = {}

  def __init__(self):  
    self.VEH = ""
    self.REF = ""
    self.UCE = ""
    self.NOM = ""
    self.cfg = []
    self.req = {}
    self.dat = {}

def acf_find_in_sirev( ref2, platform ):
  global errone
  global zip
  global zipflist
  
  if len(list(errone.keys()))==0:
    se=zip.open('SIREV_ERRONE.dat')
    cont=se.read()
    for l in cont.split(b'\n'):
      li = l.split(b'/')
      if len(li)==6 and li[0]==platform:
        errone[li[2]] = li[3]
  
  while( ref2 in list(errone.keys())):
    #print 'e:',ref2,errone[ref2] 
    ref2 = errone[ref2]
    
  return ref2

def acf_loadModules( de, refdata, platform ):
  ''' load modules from CONFIG database'''
  
  global acfFile
  global zip
  global zipflist
  
  for file in os.listdir(".."):
    if file.endswith('.acf'):
      acfFile = '../'+file
      break
      
  if acfFile=='':
    print("ERROR: Configuration database not found")
    exit()
  else:
    print("Configuration database: ", acfFile)
    
  zip=zipfile.ZipFile(acfFile)
  zip.setpassword(b'A710FBD006342FC8')
  zipflist = zip.namelist()

  module_list = []

  for r in refdata.split(';'):
    try:
      idf, r1 = r.split(':')
      ref1,ref2 = r1.split(' ')
    except:
      continue

    if ref2+'.dat' not in zipflist:
      ref2 = acf_find_in_sirev( ref2, platform )

    m = {}

    m['idf'] = idf
    m['sref'] = ref2
    m['mo']=''
    m['dst'] = ''
    m['ecuname'] = ''
    m['startDiagReq'] = '10C0'
    if ref2 + '.dat' in zipflist:
      modf = zip.open(ref2 + '.dat')
      m['mo'] = pickle.load(modf)

    for k in de:
      if k['idf']==idf:
        m['dst'] = k['dst']
        m['startDiagReq'] = k['startDiagReq']
        m['ecuname'] = k['ecuname']
        break

    module_list.append(m)

  return module_list
