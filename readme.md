## fontstep.py
fontstep is a little python-script to run some build-steps in FontLab for deploying fonts

### Actions you can control:

* copysave - creates a copy of the font with a new name
* metric - set metrics according to other glyphs
* delete - delete sepecific glyphs
* decompose - decompose and remove overlaps
* copy - copy specific glyphs
* autoUnicode - auto unicode the whole font 
* unicode - set unicode-point with UID attribute
* copysave - creates  a copy of the font with a new name
* saveTTF - save the current font as TrueType-Font (TTF)
* saveOTF - save the current font as OpenType-Font (CFF)
* saveJSON - save some information about the current font as JSON
* save - save current font

### Requirements
To run the File you have to have following software installed:

* FontLab 5.x on Mac OS X
* robofab (updated build)


## Control file
The whole process is controlled by a single file along with the FontLab-Fontfile. The control file must have the name `fontstep.xml` and must be in the same folder like the Fontfile.

### Directory structure

```
 - Folder
     Fontfile.vfb
     fontstep.xml
```

## Define control file
The `fontstep.xml` is a regular XML-File. It has a strict structure like described here. The fontstep.py doesn't allow mistakes and will break otherwise.


### Step structure
The `fontstep.xml` has a `font`-tag as root-element. All tasks are in a `step`-tag. All `step`-tag *must* have an `action`-attribute. 


```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="{{name of action}}"/>
    <step action="{{name of action}}">
        ...
    </step>
</font>
```

## Available steps
For the `action`-attribute you can have one of the steps. Described in the following paragraphs.


### copysave (action)
Creates a copy of the font with a new name with following naming scheme: `%Y%m%d-%H%M_generated.vfb`. Resulting in names like: `20130824-2301_generated.vfb`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="copysave"/>
</font>
```

### metrics (action)
With the metrics step you can set the left margin (attribute `left`), the right margin (attribute `right`) and the width (attribute `width`) of a glyph according to these attributes of an other glyph. You can set all three values or just one or two.

The syntax to set a glyph is: 
```
<glyph PSName="{{name of glyph to set attributes}}" left="{{def}}" right="{{def}}" width="{{def}}"/>
```

As for the definition of the values you can use the following syntax:

```
left({{name of the glyph to get the left margin}})
or
right({{name of the glyph to get the right margin}})
or
width({{name of the glyph to get the width}})
```

#### Helpers for classes
For all the glyph references you can use a glyph-name or a class name (as defined in FontLab). If you would like to get a single value from a group you can use the helpers `min()` and `max()`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <!-- The character with the name yen gets decomposed and all overlaps removed -->
    <step action="metrics">
        <!-- parenright gets the left margin set to the right margin of parenleft. It also gets the width of  parenleft -->
        <glyph PSName="parenright" left="right(parenleft)" width="width(parenleft)"/>
        
        <!-- backslash gets the right margin set to the right left of slash.-->
        <glyph PSName="backslash" right="left(slash)"/>
        
        <!-- all glyphs in the class MathSign (defined in FontLab) get the width of the glyph plus -->
        <glyph PSName="@MathSign" width="width(plus)"/>
        
        <!-- all glyphs in the class TabNumber (defined in FontLab) get the of the widest glyph in the class TabNumber -->
        <glyph PSName="@TabNumber" width="max(width(@TabNumber))"/>
    </step>
</font>
```

### delete (action)
Deletes a specific glyph

```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <!-- the characters with the name quote_helper and dot_helper get deleted-->
    <step action="delete">
        <glyph PSName="quote_helper"/>
        <glyph PSName="dot_helper"/>
    </step>
</font>
```

### decompose (action)
A specific glyph get decomposed and all overlaps removed

```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <!-- the characters with the name yen and dollar get decomposed and all overlaps removed-->
    <step action="decompose">
        <glyph PSName="yen"/>
        <glyph PSName="dollar"/>
    </step>
</font>
```

### copy (action)
A specific glyph get the content of an other glyph

```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <!-- the character with the name a gets created and the content of glyph A gets copied to it -->
    <step action="copy">
        <glyph PSName="a">
            <base PSName="A"/>
        </glyph>
    </step>
</font>
```

### autoUnicode (action)
All known characters (by name) get an unicode-point 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="autoUnicode"/>
</font>
```
### unicode (action)
Some specific glyphs get an unicode-point (decimal) 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="unicode">
        <glyph PSName="logo" UID="57344"/>
        <glyph PSName="zero.fitted" UID="63033"/>
        <glyph PSName="one.fitted" UID="63196"/>
        <glyph PSName="two.fitted" UID="63034"/>
        <glyph PSName="three.fitted" UID="63035"/>
        <glyph PSName="four.fitted" UID="63036"/>
        <glyph PSName="five.fitted" UID="63037"/>
        <glyph PSName="six.fitted" UID="63038"/>
        <glyph PSName="seven.fitted" UID="63039"/>
        <glyph PSName="eight.fitted" UID="63040"/>
        <glyph PSName="nine.fitted" UID="63041"/>
    </step>
</font>
```

### saveTTF (action)
Saves the current font as a PC TrueType/TT OpenType font (TTF). Int the `name`-attribute you can define the filename.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="saveTTF" name="../build/SplitBean-Regular.ttf"/>
</font>
```

### saveOTF (action)
Saves the current font as a PS OpenType (CFF-based) font (OTF). With the `name`-attribute you can define the filename.
```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="saveOTF" name="../build/SplitBean-Regular.otf"/>
</font>
```

### saveJSON (action)
Save some information about the current font as JSON. Int the `name`-attribute you can define the filename.
```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="saveJSON" name="../build/SplitBean-Regular.json"/>
</font>
```

### save (action)
Saves the current font
```xml
<?xml version="1.0" encoding="UTF-8"?>
<font>
    <step action="save"/>
</font>
```