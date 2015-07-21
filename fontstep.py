#FLM: fontstep

########################################################################
#
# Processes some final steps befor deploying fonts
# The build-steps are controlled by an xml-file
#
# inspired by FLGlyphBuilder
# http://scripts.sil.org/FLGlyphBuilder
#
# todo:
# Ð error-handling
# - Code-Cleaning...
#
#
########################################################################
#
# Released under the BSD 2-Clause license:
# http://opensource.org/licenses/BSD-2-Clause
#
########################################################################

from xmllib import *
from robofab.world import CurrentFont
import json
import datetime
import re


currAction = None  # name of current step/action
currGlyph  = None  # current PSName of glyph-tag

# for components handling
currBase   = { 'base' : '', 'xScale' : 1, 'yScale' : 1, 'xShift' : 0, 'yShift' : 0 }

def start_step(attrib):
    global currAction, currGlyph

    currAction = attrib['action']
    print "Start Step: " + currAction

    if currAction == 'copysave':
        print "Savepaht: " + saveFontCopy()

    if currAction == 'save':
        print "Font saved. #yay"
        f.save()

    if currAction == 'saveJSON':
        print "json saved"
        writeInfoJson(attrib['name'])

    if currAction == 'orderGlyphs':
        print "order glyphs"
        orderGlyphs(attrib['by'])

    if currAction == 'saveTTF':
        print "TrueType saved"
        writeTTF(attrib['name'])

    if currAction == 'saveOTF':
        print "OpenType saved"
        writeOTF(attrib['name'])

    if currAction == 'autoUnicode':
        # do it in fontlab
        f.naked().GenerateUnicode()

        # now do it in robofab
        f.autoUnicodes()

        print "Set auto unicodes"


def end_step():
    f.update()


def start_glyph(attrib):
    global currAction, currGlyph

    # print "start glyph"
    currGlyph = attrib['PSName']

    if currAction == 'delete':
        doDelGlyphs(currGlyph)

    if currAction == 'decompose':
        doDecompose(currGlyph)

    if currAction == 'metrics':
        doMetrics(attrib)

    if currAction == 'unicode':
        doUnicode(currGlyph, attrib['UID'])

def start_base(attrib):
    global currAction, currBase

    if currAction == 'copy':
        print "Copy %s to %s" % (attrib['PSName'], currGlyph)
        copyGlyph(currGlyph, attrib['PSName'])

    if currAction == 'components':
        currBase['base'] = attrib['PSName']

def end_base():
    global currAction

    if currAction == 'components':
        doComponents()

def start_scale(attrib):
    global currAction

    if currAction == 'components':
        currBase['xScale'] = float(attrib['x'])
        currBase['yScale'] = float(attrib['y'])

def start_shift(attrib):
    global currAction

    if currAction == 'components':
        currBase['xShift'] = float(attrib['x'])
        currBase['yShift'] = float(attrib['y'])

def end_font():
    f.update()


#XML parser - could be replace by more up-to-date SAX parser
class jobXML(XMLParser):
    elements = {'glyph': [start_glyph, None],
                'base': [start_base, end_base],
                'scale': [start_scale, None],
                'shift': [start_shift, None],
                'step': [start_step, end_step],
                'font': [None,   end_font]}

########################################################################


# source: http://rosettacode.org/wiki/Determine_if_a_string_is_numeric#Python
# returns the int-value
def is_numeric(lit):
    'Return value of numeric literal string or ValueError exception'
 
    # Handle '0'
    if lit == '0': return 0
    # Hex/Binary
    litneg = lit[1:] if lit[0] == '-' else lit
    if litneg[0] == '0':
        if litneg[1] in 'xX':
            return int(lit,16)
        elif litneg[1] in 'bB':
            return int(lit,2)
        else:
            try:
                return int(lit,8)
            except ValueError:
                pass
 
    # Int/Float/Complex
    try:
        return int(lit)
    except ValueError:
        pass
    try:
        return float(lit)
    except ValueError:
        pass
    return complex(lit)


def doUnicode(glyphname, unicode):
    print "Unicode of %s to %s" % (glyphname, unicode)

    if not unicode:
        f[glyphname].autoUnicodes()
    else:
        f[glyphname].unicodes = [is_numeric(unicode)]

    f[glyphname].update()


# do special decompose for some glyphs
def doDecompose(glyphname):

    glyphNames = []

    if glyphname[0] == "@":
        glyphNames.extend(getGlyphClass(glyphname))
    else:
        glyphNames.append(glyphname)

    for cIdx in range(len(glyphNames)):
        
        #print "remove overlaps of composed glyphs"
        g = f[glyphNames[cIdx]]
        # multiple decompose because of strange FontLab behaviour...
        g.decompose()
        g.decompose()
        g.decompose()
        # multiple remove to clean up straight lines with points inbetween
        g.removeOverlap()
        g.removeOverlap()
        g.removeOverlap()
        g.update()



def doDelGlyphs(glyphname):
    f.removeGlyph(glyphname)
    print "DEL: " + glyphname


def copyGlyph(copyName, origName):
    f.removeGlyph(copyName)
    f[copyName].appendGlyph(f[origName].copy())
    f[copyName].width = f[origName].width


def getDateString():
    #timestamp of now  (used to set in filename)
    now = datetime.datetime.now()
    nowStr = now.strftime("%Y%m%d-%H%M")
    return nowStr


def getPathString():

    fontName = f.info.postscriptFullName.replace(" ", "_")
    fontName = re.sub(r"[^a-zA-Z0-9]]", "", fontName)

    fontPathOrig = f.path

    separatorPosition = fontPathOrig.rfind("/")
    fontPathNew = fontPathOrig[0:separatorPosition]
    fontPathNew = fontPathNew + "/"

    return fontPathNew


def saveFontCopy():

    fontPathNew = getPathString() + getDateString() + "_generated.vfb"

    f.save(fontPathNew)
    return fontPathNew


def getMetrics(strFunction):

    pattern = r'(\w[\w\d_]*)\((.*)\)$'
    match = re.match(pattern, strFunction)

    # print list(match.groups())

    if match:

        functionName = list(match.groups())[0]
        functionArg = list(match.groups())[1]
        returnVal = []

        # if the first argument starts with @ it is a group
        glyphNames = []
        if functionArg[0] == "@":
            glyphNames.extend(getGlyphClass(functionArg))
        else:
            glyphNames.append(functionArg)

        for cIdx in range(len(glyphNames)):
            #g = f[glyphNames[cIdx]]

            if functionName == 'left':
                returnVal.append(f[glyphNames[cIdx]].leftMargin)
            if functionName == 'right':
                returnVal.append(f[glyphNames[cIdx]].rightMargin)
            if functionName == 'width':
                returnVal.append(f[glyphNames[cIdx]].width)
            if functionName == 'max':
                returnVal.append(max(getMetrics(functionArg)))
            if functionName == 'min':
                returnVal.append(min(getMetrics(functionArg)))

        # print "parse: " + strFunction + " to %s"%returnVal

        if len(returnVal) == 1:
            return returnVal[0]
        else:
            return returnVal

    else:
        print "uuuh! no function in " + strFunction


def doComponents():
    global currBase, currGlyph

    g = f[ currGlyph ]  

    g.appendComponent( currBase['base'], (currBase['xShift'], currBase['yShift']), (currBase['xScale'], currBase['yScale']) )
    
    # reset defaults
    currBase['base'] = ''
    currBase['xShift'] = 0
    currBase['yShift'] = 0
    currBase['xScale'] = 1
    currBase['yScale'] = 1


def doMetrics(attrib):
    lGlyph = attrib['PSName']

    glyphNames = []

    if lGlyph[0] == "@":
        glyphNames.extend(getGlyphClass(lGlyph))
    else:
        glyphNames.append(lGlyph)

    for cIdx in range(len(glyphNames)):
        g = f[glyphNames[cIdx]]

        if 'left' in attrib:
            g.leftMargin = getMetrics(attrib['left'])
        if 'right' in attrib:
            g.rightMargin = getMetrics(attrib['right'])
        if 'width' in attrib:
            # print attrib['width']
            # print getMetrics(attrib['width'])
            g.width = getMetrics(attrib['width'])
        if 'centeredWidth' in attrib:
            newWidth = getMetrics(attrib['centeredWidth'])
            g.leftMargin = g.leftMargin + (( newWidth - g.width ) / 2) 
            g.width = newWidth

        g.update()


def getClasses():

    out = {}

    flF = fl.font
    if flF is not None:
        classes = flF.classes

        for cIdx in range(len(classes)):
            cName = classes[cIdx].split(":")[0].strip()
            cName = cName.lstrip(".")
            cGlyphs = classes[cIdx].split(":")[1].strip()
            cGlyphs = cGlyphs.replace("'", "").split(" ")
            out[cName] = cGlyphs
    else:
        print "Error. No FontLab?!"

    return out


def getGlyphClass(classNameRaw):
    className = classNameRaw.replace("@", "")

    # todo: bring in getClasses !
    flF = fl.font
    if flF is not None:
        classes = flF.classes

        for cIdx in range(len(classes)):
            cName = classes[cIdx].split(":")[0].strip()
            cName = cName.lstrip(".")

            if cName == className:
                cGlyphs = classes[cIdx].split(":")[1].strip()
                cGlyphs = cGlyphs.replace("'", "").split(" ")
                return cGlyphs
    else:
        print "Error. No FontLab?!"


def orderGlyphs(sortBy):
    f.update()
    fl.CallCommand(fl_cmd.EditSelectAll)
    fl.CallCommand(fl_cmd.FontModeNames)
    fl.CallCommand(fl_cmd.FontSortByName)
    f.update()


def writeTTF(fileName):
    # PC TrueType/TT OpenType font (TTF)
    writeFontFL(ftTRUETYPE, getPathString() + fileName)


def writeOTF(fileName):
    # PS OpenType (CFF-based) font (OTF)
    writeFontFL(ftOPENTYPE, getPathString() + fileName)


def writeFontFL(fontType, path):
    fl.GenerateFont(fontType, path)



def getInfoGlyph(glyphName):
    outCurrent = {}

    if f.has_key(glyphName):
        glyph = f[glyphName]
        outCurrent['name'] = glyph.name

        if (len(glyph.unicodes) > 0):
            # print first unicode
            outCurrent['unicode'] = glyph.unicodes[0]
            outCurrent['unicodeHex'] = hex(glyph.unicodes[0])[2:].upper()
            outCurrent['unicodeChar'] = unichr(glyph.unicodes[0])

        outCurrent['width'] = glyph.width
        outCurrent['left'] = glyph.leftMargin
        outCurrent['right'] = glyph.rightMargin

    return outCurrent


def writeInfoJson(fileName):

    outJson = {}
    outJson["chars"] = []

    for glyph in f.glyphs:
        outJson["chars"].append( getInfoGlyph(glyph.name) )

    outJson["classes"] = []

    classList = getClasses()
    #print list(classList)
    for className in list(classList):
        outCurrent = {}
        outCurrent['name'] = className
        outCurrent['chars'] = []

        for char in getGlyphClass(className):
            outCurrent['chars'].append(getInfoGlyph(char))

        outJson["classes"].append(outCurrent)

    outJson["info"] = {}
    outJson["info"]["versionMajor"] = f.info.versionMajor
    outJson["info"]["versionMinor"] = f.info.versionMinor
    outJson["info"]["version"] = f.info.versionMajor + (f.info.versionMinor / 1000.0)

    jsonPathNew = getPathString() + fileName

    fOut = open(jsonPathNew, "w")

    #fOut.write('{ "chars" :')
    fOut.write(json.dumps(outJson,indent=4))
    #fOut.write('}')
    fOut.close()


# now read in the xml and run te commands
########################################################################

f = CurrentFont()

ctlfile = r""+f.path[0:f.path.rfind("/")+1]+"fontstep.xml"  # see fileext

fh = open(ctlfile, "r")
print "open: " + ctlfile
if fh:
    xml = jobXML()

    print "start parse" 
    strR = fh.readline()
    while strR:
        xml.feed(strR)
        strR = fh.readline()

    print "end parse" 
	
    xml.close
    fh.close
