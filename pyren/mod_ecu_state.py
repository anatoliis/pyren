#!/usr/bin/env python

from mod_ecu_mnemonic   import *
from mod_utils          import Choice
from xml.dom.minidom    import parse
from xml.dom.minidom    import parseString
import xml.dom.minidom
import mod_globals

def get_state( st, mn, se, elm, calc ):
  comp = st.computation
  comp = comp.replace("&amp;","&")
  for m in sorted(st.mnemolist, key=len, reverse=True):
    hex_val = get_mnemonic( mn[m], se, elm )
    comp = comp.replace(m, "0x"+hex_val) 
  tmp_val = calc.calculate(comp)
  
  if str(tmp_val).encode("utf-8") in st.caracter.keys():
    st.value = st.caracter[str(tmp_val).encode("utf-8")]
  else:
    st.value = ""

  csv_val = unicode(st.value) if mod_globals.opt_csv_human else tmp_val
  if mod_globals.os=='android':
    st.value = " "*(8-len(st.value)/2) + st.value
    return "%-6s %-41s %-16s"%(st.codeMR,st.label,st.value), st.helps, csv_val
  else:
    st.value = " "*(16-len(st.value)/2) + st.value
    return "%-6s %-50s %-20s"%(st.codeMR,st.label,st.value), st.helps, csv_val

class ecu_state:

  name        = ""
  agcdRef     = ""
  codeMR      = ""
  label       = ""
  value       = ""
  type        = ""
  helps       = []
  caracter    = {}
  computation = ""
  mnemolist   = []
  
  def __str__(self):
    hlps = '['
    for h in self.helps: hlps += '\'' + h + '\'\n'
    hlps += ']'

    chrc = '{\n'
    for c in self.caracter.keys(): chrc += c + ' : \'' + self.caracter[c] + '\'\n'
    chrc += '}'
  
    out = '''
  name        = %s
  agcdRef     = %s
  codeMR      = %s
  label       = %s
  value       = %s
  type        = %s
  helps       = %s
  caracter    = %s
  computation = %s
  mnemolist   = %s
    ''' % (
           self.name, self.agcdRef, self.codeMR, self.label, self.value, self.type,
           hlps, chrc, self.computation, self.mnemolist)
    return pyren_encode(out)  

  def __init__(self, st, opt, tran ):
    self.name = st.getAttribute("name")
    self.agcdRef = st.getAttribute("agcdRef")
    self.codeMR  = st.getAttribute("codeMR")
    
    Label = st.getElementsByTagName("Label")
    codetext = Label.item(0).getAttribute("codetext")
    defaultText = Label.item(0).getAttribute("defaultText")
    self.label = ""
    if codetext:
      if codetext in tran.keys():
        self.label = tran[codetext]
      elif defaultText:
        self.label = defaultText
      
    self.helps = []
    Helps = st.getElementsByTagName("Helps")
    if Helps:
      for hl in Helps:
        Lines = hl.getElementsByTagName("Line")
        if Lines:
          for ln in Lines:
            line = ""
            Label = ln.getElementsByTagName("Label")
            if Label:
              for la in Label:
                codetext = la.getAttribute("codetext")
                defaultText = la.getAttribute("defaultText")
                if codetext:
                  if codetext in tran.keys():
                    line = line + tran[codetext]
                  elif defaultText:
                    line = line + defaultText
            self.helps.append(line+'\n')

    self.caracter = {}
    Interpretation = st.getElementsByTagName("Interpretation")
    if Interpretation:
      for cor in Interpretation:
        Correspondance = cor.getElementsByTagName("Correspondance")
        if Correspondance:
          for co in Correspondance:
            ivalue = co.getAttribute("value")
            codetext  = co.getAttribute("codetext")
            defaultText = co.getAttribute("defaultText")
            itext = ""
            if codetext:
              if codetext in tran.keys():
                itext = tran[codetext]
              elif defaultText:
                itext = defaultText
              self.caracter[ivalue]=itext
    
    xmlstr = opt["State\\"+self.name]
    odom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
    odoc = odom.documentElement
    
    self.computation = ""
    Computation = odoc.getElementsByTagName("Computation")
    if Computation:
      for cmpt in Computation:
        self.type = cmpt.getAttribute("type")
        tmp = cmpt.getElementsByTagName("Value").item(0).firstChild.nodeValue
        self.computation = tmp.replace(" ","").replace("&amp;","&")
        
        self.mnemolist = []
        Mnemo = cmpt.getElementsByTagName("Mnemo")
        if Mnemo:
          for mn in Mnemo:
            self.mnemolist.append(mn.getAttribute("name"))

class ecu_states:
 
  def __init__(self, state_list, mdoc, opt, tran ):
    States = mdoc.getElementsByTagName("State")
    if States:
      for st in States:
        state = ecu_state( st, opt, tran )
        state_list[state.name] = state
        
