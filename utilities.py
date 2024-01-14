import webcolors
import fitz
from fitz.utils import rule_dict
from tkinter import messagebox

annot_name='Chapman_'

def closest_colour(requested_colour):
    min_colours = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

def get_colour_name(requested_colour):
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    if closest_name=='lime': closest_name='green'
    if closest_name=='blueviolet': closest_name='violet'
    return closest_name

def converttoRGB(c):
    a=list(c)
    a[0]=a[0]*255
    a[1]=a[1]*255
    a[2]=a[2]*255
    return a


red = (1, 0, 0)
orange = (1, 0.65, 0)
yellow = (1, 1, 0.2)
green = (0, 1, 0)
blue = (0, 0, 1)
indigo = (0.29, 0, 0.51)
violet = (0.54, 0.17, 0.89)
black = (0, 0, 0)

def get_colour(tags):
    # returns colour code for selection
    colour = black  # default

    for tag in tags:
        if tag == 'red':
            return red
        elif tag == 'orange':
            return orange
        elif tag == 'yellow':
            return yellow
        elif tag == 'green':
            return green
        elif tag == 'blue':
            return blue
        elif tag == 'indigo':
            return indigo
        elif tag == 'violet':
            return violet
        elif tag == 'black':
            return black
        else:
            return black
    return colour

def get_style(tags):
    for tag in tags:
        if tag=='plain':
            return 'plain'
        if tag=='bold':
            return 'bold'
        if tag=='italic':
            return 'italic'
    return 'plain'


def configColours(tree):
    tree.tag_configure('black', foreground='black')
    tree.tag_configure('red', foreground='red')
    tree.tag_configure('orange', foreground='orange')
    tree.tag_configure('yellow', foreground='yellow')
    tree.tag_configure('green', foreground='green')
    tree.tag_configure('blue', foreground='blue')
    tree.tag_configure('indigo', foreground='indigo')
    tree.tag_configure('violet', foreground='violet')

def configStyles(tree):
    tree.tag_configure('plain', font=('Helvetica',13))
    tree.tag_configure('italic', font=('Helvetica',13,'italic'))
    tree.tag_configure('bold', font=('Helvetica',13,'bold'))
    tree.tag_configure('bold-italic', font=('Helvetica',13,'bold italic'))

def configHover(tree):
    tree.tag_configure('hovered', font=('Helvetica',13,'underline'))
    tree.tag_configure('hovered-italic', font=('Helvetica',13,'underline italic'))
    tree.tag_configure('hovered-bold', font=('Helvetica',13,'underline bold'))
    tree.tag_configure('hovered-bold-italic', font=('Helvetica',13,'underline bold italic'))


def parse_page_string(doc, txt):
    # txt = "1,2-3,4,5" etc where these refer to page labels
    # if txt=="" then return all pages
    # returns list of pages or None if bad page labels provided
    l = []
    if txt == "":  # i.e. a blank entry then all pages
        for i in range(0, doc.page_count):
            l.append(i)
    else:
        # parse each bit
        bits = txt.split(',')  # split by comma
        for bit in bits:
            if bit.find('-') > -1:
                more_bits = bit.split('-')
                more_bits[0]=more_bits[0].strip()
                more_bits[1]=more_bits[1].strip()
                if len(doc.get_page_numbers(more_bits[0]))==0  or len(doc.get_page_numbers(more_bits[1]))==0:
                    #bad page reference
                    return None
                st=doc.get_page_numbers(more_bits[0])[0]
                en=doc.get_page_numbers(more_bits[1])[0]
                if en>st:
                    for i in range(st, en + 1):
                        l.append(i)
                else:
                    #bad page references
                    return None
            else:
                bit=bit.strip()
                if len(doc.get_page_numbers(bit))==0:
                    #bad page references
                    return None
                l.append(doc.get_page_numbers(bit)[0])
    return l


def max_depth(doc):
    # returns max-depth of bookmarks
    toc = doc.get_toc()
    max_depth = 0
    for t in toc:
        level = t[0]
        if level > max_depth: max_depth = level
    return max_depth


def add_default_label(doc):
    labels = doc.get_labels_rule_dict()
    if len(labels) == 0:  # if no labels create default one
        labels.append({'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1})
    doc.set_page_labels(labels)

def get_labels_rule_dict(doc):
    ls=doc._get_page_labels()
    l=[]
    for item in ls:
        l.append(rule_dict(item))
    return l

def selectWord(page, point):
    #selects the word at this point if found
    #returns the word (rect, text) or None
    w=page.getWord(point)
    if w:
        page.select(w[0].tl, w[0].br)
        return w
    return None

def getWord(page,point):
    #returns tuple of rect and text of word at point point
    #or None if none at this point
    for w in page.get_text('words'):
        rect=fitz.Rect(w[:4])
        if point in rect:
            return (rect, w[4])
    return None

def getchar(page,point):
    #returns the character at point on page
    dict = page.get_text('rawdict')
    blocks = [b for b in dict['blocks'] if point in fitz.Rect(b['bbox']) and b['type'] == 0]
    if len(blocks) > 0:
        lines = [l for l in blocks[0]['lines'] if point in fitz.Rect(l['bbox'])]
        if len(lines) > 0:
            spans = [s for s in lines[0]['spans'] if point in fitz.Rect(s['bbox'])]
            if len(spans) > 0:
                chars = [c for c in spans[0]['chars'] if point in fitz.Rect(c['bbox'])]
                if len(chars) > 0:
                    return chars[0]
    return None


def remove_draw_links(page):
    #removes drawn links on page
    for annot in page.annots():
        if annot.info['id'].find(annot_name + "linkunderlining") > -1:
            page.delete_annot(annot)

def draw_links(page):
    #adds underlining for links on page
    fitz.TOOLS.set_annot_stem(annot_name + "linkunderlining")
    lnks = page.get_links()
    for lnk in lnks:
        annot=page.add_underline_annot(lnk['from'])
        blue = (0, 0, 1)
        annot.set_colors({"stroke":blue})
        annot.update()

def link_clicked(page,point):
    #returns link if point within link
    #point needs to be converted to pdfPoint
    lnks = page.get_links()
    for lnk in lnks:
        if point in fitz.Rect(lnk['from']):
            return lnk
    return None

def inTextArea(page,point):
    #returns True if in text area or else False
    dict = page.get_text('rawdict')
    blocks=[block for block in page.get_text('rawdict')['blocks'] if block['type']==0]
    for block in blocks:
        if point in fitz.Rect(block['bbox']):
            return True
    return False

def isAnnotArea(page, point):
    #returns annot.xref if point is within annotarea that is not a selection
    #else None
    for annot in page.annots():
        if annot.vertices:
            for quad in verticestoQuads(annot.vertices):
                if (point in quad.rect and not annot.info['id'].find(annot_name + 'select-highlight') > -1):
                    return annot.xref
    return None

def gettextselectedHighlights(page):
    #gets the text from the selected highlights
    txt=''
    for annotxref in page.selectedAnnots:
        quads = []
        annot=page.loadAnnot(annotxref)
        quads.extend(verticestoQuads(annot.vertices))
        if quads:
            # first quad
            start = fitz.Point(quads[0].rect.tl)
            start.y -= 0.1  # minor adjustment required
            # loast quad
            end = fitz.Point(quads[-1].rect.br)
            end.y += 0.1  # minor adjustment required
            spans = page.getselectSpans(start, end)
            for s in spans:
                txt += ''.join([c['c'] for c in s['chars']])
    return txt


def getselectedText(page):
    quads=[]
    txt=''
    [quads.extend(verticestoQuads(annot.vertices)) for annot in page.annots() if annot.info['id'].find(annot_name + "select-highlight") > -1]
    if quads:
        #first quad
        start=fitz.Point(quads[0].rect.tl)
        start.y-=0.1 #minor adjustment required
        #loast quad
        end=fitz.Point(quads[-1].rect.br)
        end.y+=0.1 #minor adjustment required
        spans=page.getselectSpans(start,end)
        for s in spans:
            txt += ''.join([c['c'] for c in s['chars']])
    return txt

def deselectAnnot(page):
    [page.deleteAnnot(annot) for annot in page.annots() if annot.info['id'].find(annot_name + "selected-highlight-border") > -1]

def removeSelectedAnnots(page):
    page.deselectAnnot()
    for annotxref in page.selectedAnnots:
        annot=page.loadAnnot(annotxref)
        page.deleteAnnot(annot)
    page.selectedAnnots.clear()

def selectAnnot(page,point, clearexisting=True):
    #if there is annot at point, adds a border to it
    #and removes the border from the others if clearexisting=True
    #adds the selected annotxref to list if clearexisting=False
    #returns xref of the selected annot

    annotxref=page.isAnnotArea(point)
    if annotxref:
        if clearexisting:
            page.deselectAnnot() #deselect the other annots
            page.selectedAnnots.clear()
        fitz.TOOLS.set_annot_stem(annot_name + 'selected-highlight-border')
        annot=page.loadAnnot(annotxref)
        quads=verticestoQuads(annot.vertices)
        for quad in quads:
            a=page.addRectAnnot(quad.rect)
            a.setColors({'stroke':(0.6,0.8,1)})
            a.update()
        page.selectedAnnots.append(annotxref)
        return annotxref

def highlightSelection(page, colour=None):
    #removes the existing selection and
    #highlights the selected annotations
    if not colour: colour=(1,1,0) #default is yellow
    fitz.TOOLS.set_annot_stem(annot_name + 'highlight')
    quads=[]
    [quads.extend(verticestoQuads(annot.vertices)) for annot in page.annots() if annot.info['id'].find(annot_name + "select-highlight") > -1]
    if quads:
        page.removeSelection()
        annot=page.addHighlightAnnot(quads)
        annot.setColors({"stroke": colour})
        annot.setBorder(width=10)
        annot.update()
        return annot.xref
    return None

def removeSelection(page):
    #removes the select annotations
    [page.delete_annot(annot) for annot in page.annots() if annot.info['id'].find(annot_name + "select-highlight") > -1]

def select(page, startPoint, endPoint):
    #removes any existing selection and then
    #sets the text between startPoint and endPoint to light-blue
    #returns the xref of the annot or None if no selection added
    fitz.TOOLS.set_annot_stem(annot_name + "select-highlight")
    rects=[fitz.Rect(s['bbox']) for s in page.getselectSpans(startPoint,endPoint)]
    if rects:
        page.removeSelection()
        annot = page.add_highlight_annot(rects)
        annot.set_colors({"stroke": (0.6,0.8,1)}) #light blue
        annot.update()
        return annot.xref
    return None

def getselectSpans(page, startPoint, endPoint):

    def intersect(A,B):
        #returns True if rect A intersects rect B
        right=min(A.br.x, B.br.x)
        left=max(A.bl.x, B.bl.x)
        left=min(left,right)
        bottom=min(A.br.y,B.br.y)
        top=max(A.tr.y,B.tr.y)
        top=min(bottom,top)
        newrect=fitz.Rect(left,top,right,bottom)
        if newrect.width * newrect.height==0:
            return False
        return True

    def heightSpan(span):
        r=fitz.Rect(span['bbox'])
        return r.height

    def inRectsBits(A,C,D):
        #returns true if
        #A intersects with any B, C, or D
        #A.tl in rect D
        mp=fitz.Point(A.bl.x+A.width/2, A.tl.y+A.height/2)
        if mp in C or mp in D:
            return True
        return False
        if intersect(A,C) or intersect(A,D): return True
        return False

    sp=[]
    pageRect = page.rect
    B = fitz.Rect(pageRect[0], startPoint.y, pageRect[2], endPoint.y) #big rect

    dict=page.get_text('rawdict')
    blocks = [b for b in dict['blocks'] if b['type'] == 0 and intersect(fitz.Rect(b['bbox']),B)]
    for block in blocks:
        lines=[l for l in block['lines'] if intersect(fitz.Rect(l['bbox']),B)]
        for line in lines:
            spans=[s for s in line['spans'] if intersect(fitz.Rect(s['bbox']),B)]
            sp.extend(spans)
    if sp:
        height1=heightSpan(sp[0])
        height2=heightSpan(sp[-1])
        B = fitz.Rect(pageRect[0], startPoint.y+height1, pageRect[2], max(startPoint.y+height1,endPoint.y-height2))  # big rect

        C = fitz.Rect(0, 0, startPoint.x, startPoint.y)
        D = fitz.Rect(endPoint.x, endPoint.y, pageRect[2], pageRect[3])

#        C=fitz.Rect(startPoint.x,startPoint.y, pageRect[2],startPoint.y+height1) #top rect
#        D=fitz.Rect(pageRect[0],endPoint.y-height2, endPoint.x,endPoint.y) #bottom  rect

        chars=[]
        for s in sp:
            chars.extend([c for c in s['chars'] if not inRectsBits(fitz.Rect(c['bbox']),C,D)])
        print(''.join([c['c'] for c in chars]))

    return sp

    lines=[]
    spans = []
    if not startPoint or not endPoint: return spans
    pageRect = page.rect
    bigrect = fitz.Rect(pageRect[0], startPoint.y, pageRect[2], endPoint.y)
    cutoutrect1=fitz.Rect(0,0,startPoint.x,startPoint.y)
    cutoutrect2=fitz.Rect(endPoint.x,endPoint.y,pageRect[2],pageRect[3])
    dict = page.getText('rawdict')
    blocks = [b for b in dict['blocks'] if b['type'] == 0]
    for block in blocks:
        ls=[l for l in block['lines'] if fitz.Point(fitz.Rect(l['bbox']).tl) in bigrect and fitz.Point(fitz.Rect(l['bbox']).br) in bigrect and not (fitz.Point(fitz.Rect(l['bbox']).tr) in cutoutrect1 or fitz.Point(fitz.Rect(l['bbox']).bl) in cutoutrect2)]
        lines.extend(ls)
        for line in lines:
            sp = [s for s in line['spans'] if fitz.Point(fitz.Rect(s['bbox']).tl) in bigrect and fitz.Point(fitz.Rect(s['bbox']).br) in bigrect and not (fitz.Point(fitz.Rect(s['bbox']).tr) in cutoutrect1 or fitz.Point(fitz.Rect(s['bbox']).bl) in cutoutrect2)]
            line['spans']=sp
#            spans.extend(sp)
    #Deal with first and last lines
    if len(lines)>0:
        #first line
        for span in lines[0]['spans']:
            chars=[c for c in span['chars'] if c['bbox'][0] > startPoint.x-0.1]
            span['chars']=chars
            print(''.join([c['c'] for c in chars]))
            if len(chars)>0:
                rect=fitz.Rect(span['bbox'])
                rect[0]=fitz.Point(fitz.Rect(chars[0]['bbox']).tl).x
                rect[1]=fitz.Point(fitz.Rect(chars[0]['bbox']).tl).y
                span['bbox']=rect[:4]
                lines[0]['span']=span
        #last line
        for span in lines[-1]['spans']:
            chars=[c for c in span['chars'] if c['bbox'][2] < endPoint.x+0.1]
            span['chars']=chars
            print(''.join([c['c'] for c in chars]))
            if len(chars)>0:
                rect=fitz.Rect(span['bbox'])
                rect[2]=fitz.Point(fitz.Rect(chars[-1]['bbox']).br).x
                rect[3]=fitz.Point(fitz.Rect(chars[-1]['bbox']).br).y
                span['bbox']=rect[:4]
                lines[-1]['span']=span
    for line in lines:
        for span in line['spans']:
            if span['chars']: spans.append(span)
    return spans

def verticestoQuads(vertices):
    quads = []
    if not vertices: return quads
    for i in range(0, len(vertices), 4):
        ul = vertices[i]
        ur = vertices[i + 1]
        ll = vertices[i + 2]
        lr = vertices[i + 3]
        quad = fitz.Quad(ul, ur, ll, lr)
        quads.append(quad)
    return quads

selectedAnnots=[]