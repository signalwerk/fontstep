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
# – error-handling
# - Code-Cleaning...
#
#
########################################################################
#
# This file is dual-licensed:
# BSD 2-Clause license  http://opensource.org/licenses/BSD-2-Clause
# GPL v3                http://opensource.org/licenses/GPL-3.0
#
########################################################################

from xmllib import *
from robofab.world import CurrentFont
import json
import datetime
import re


currAction = None
currGlyph = None


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
    print "Copy %s to %s" % (currGlyph, attrib['PSName'])
    copyGlyph(currGlyph, attrib['PSName'])


def end_font():
    f.update()


#XML parser - could be replace by more up-to-date SAX parser
class jobXML(XMLParser):
    elements = {'glyph': [start_glyph,  None],
                'base': [start_base,   None],
                'step': [start_step,   None],
                'font': [None,   end_font]}

########################################################################


def doUnicode(glyphname, unicode):
    print "Unicode of %s to %s" % (glyphname, unicode)

    f[glyphname].unicodes = [int(unicode)]
    f[glyphname].update()


# do special decompose for some glyphs
def doDecompose(glyphname):
    #print "remove overlaps of composed glyphs"
    g = f[glyphname]
    g.decompose()
    # multiple remove to clean up straight lines with points inbetween
    g.removeOverlap()
    g.removeOverlap()
    g.removeOverlap()


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


def getGlyphClass(classNameRaw):
    className = classNameRaw.replace("@", "")

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


def writeInfoJson(fileName):

    outJson = []

    for glyph in f.glyphs:

        outCurrent = {}
        outCurrent['name'] = glyph.name

        # is the char with .fitted in the name (for numbers)
        if outCurrent['name'].endswith(".fitted"):
            outCurrent['fitted'] = 1

        if (len(glyph.unicodes) > 0):
            outCurrent['unicode'] = glyph.unicodes[0]
            outCurrent['unicodeHex'] = hex(glyph.unicodes[0])[2:].upper()
            # is in  Private Use Areas
            if outCurrent['unicode'] >= int("E000", 16) and outCurrent['unicode'] <= int("F8FF", 16):
                outCurrent['private'] = 1

        outCurrent['width'] = glyph.width
        outCurrent['left'] = glyph.leftMargin
        outCurrent['right'] = glyph.rightMargin

        outJson.append(outCurrent)

    jsonPathNew = getPathString() + fileName

    fOut = open(jsonPathNew, "w")

    fOut.write('{ "chars" :')
    fOut.write(json.dumps(outJson,indent=4))
    fOut.write('}')
    fOut.close()


# now read in the xml and run te commands
########################################################################

f = CurrentFont()

ctlfile = r""+f.path[0:f.path.rfind("/")+1]+"fontstep.xml"  # see fileext

fh = open(ctlfile, "r")
if fh:
    xml = jobXML()

    strR = fh.readline()
    while strR:
        xml.feed(strR)
        strR = fh.readline()

    xml.close
    fh.close
