import fontforge
import base64


weights = [ "Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black" ]
italics = [ "", "Italic" ]


short = [ "comma", "period", "colon", "semicolon" ]
rest = [ i for i in range(32, 63+1) ]

# p1 and p2 should be tuples
def pointOnLine( p1, p2, x=None, y=None):
    # assume the input makes sense
    if x is not None:
        # return the y coord for the given x on the line defined by p1 and p2
        vx = p1[0]-p2[0]
        vy = p1[1]-p2[1]

        k = (x - p2[0]) / vx
        return p2[1] + k*vy
    elif y is not None:
        # return the x coord for the given y on the line defined by p1 and p2
        vx = p1[0]-p2[0]
        vy = p1[1]-p2[1]

        k = (y - p2[1]) / vy
        return p2[0] + k*vx        
        
    return 0
    

def addSerifToOnePoppins( font ):
    one = font["one"]
    pen = one.glyphPen()

    layer = one.foreground
    contour = layer[ 0 ] # should be only one contour
    points = []
    for p in contour:
        points.append( ( p.x, p.y ) )

    serifHeight = points[1][1] - points[0][1]
    serifWidth = points[-1][0] - points[0][0]
    
    pen.moveTo( points[0] )
    pen.lineTo( points[1] )
    pen.lineTo( points[2] )
    x = pointOnLine( points[2], points[3], None, serifHeight )
    pen.lineTo( ( x, serifHeight ) )
    pen.lineTo( ( x + serifWidth, serifHeight ) )
    pen.lineTo( ( points[3][0] + serifWidth, 0 ) )
    pen.lineTo( ( points[4][0] - serifWidth, 0 ) )
    x = pointOnLine( points[4], points[5], None, serifHeight )
    pen.lineTo( ( x - serifWidth, serifHeight ) )
    pen.lineTo( ( x, serifHeight ) )
    pen.lineTo( points[5] )
    pen.closePath();


    one.width = 550
    # center in width
    one.left_side_bearing = one.right_side_bearing = (one.left_side_bearing + one.right_side_bearing)/2 

    return font


def makeNumeric( font, rules, addSerif, fileName ):
    if addSerif:
        font = addSerifToOnePoppins( font )
    allGlyphs = []
    for i in rules:
        allGlyphs += i[0]

    # clear all glyphs not mentioned in rules
    for i in allGlyphs:
        font.selection.select( ("more", None), i ) # append glyph to selection
    font.selection.invert()
    font.unlinkReferences()
    font.clear()

    for j in rules:
        glyphs = j[0]
        width = j[1]
        if width == 0: # width = 0 means that the glyph should not be changed
            continue

        font.selection.none()
        for i in glyphs:
            font.selection.select( ("more", None), i ) # append glyph to selection

        for i in font.selection.byGlyphs:
            # set width
            i.width = width
            # center in width
            i.left_side_bearing = i.right_side_bearing = (i.left_side_bearing + i.right_side_bearing)/2 

    font.generate( fileName )

    base64font = ""
    newFile = open( fileName, "rb" )
    base64font = base64.b64encode( newFile.read() )
    newFile.close()
    return base64font
    

def makeCSSfont( b64, name, weight=100, style="normal" ):
    return """@font-face{
    font-family:'""" + name + """';
    src: url(data:application/font-ttf;charset=utf-8;base64,""" + b64 + """) format('truetype');
    font-weight:""" + str(weight) + """;
    font-style: """ + style + """;
}

"""

def weightStringToNum( w ):
    return ( weights.index( w ) + 1 ) * 100

def italicToCssProperty( i ):
    return "normal" if i == "" else "italic"


fileString = ""
for addSerif in [False, True]:
    for i in italics:
        for w in weights:
            if w == "Regular" and i == "Italic":
                name = "Poppins-" + i + ".ttf"
            else:
                name = "Poppins-" + w + i + ".ttf"
            saveName = "Numeric/" + ( "S" if addSerif else "" ) + name
            cssName = "Poppins-Numeric" + ( "S" if addSerif else "" )
            try:
                f = fontforge.open( name )
            except EnvironmentError:
                continue

            # manualy set the widths for different glyph groups
            rules = [ (rest, 550), (short, 200) ]

            base64font = makeNumeric( f, rules, addSerif, saveName )
            fileString = fileString + makeCSSfont( base64font, cssName, weightStringToNum( w ), italicToCssProperty( i ) )


css = open( "fonts.css", "w" )
css.write( fileString )
css.close()


