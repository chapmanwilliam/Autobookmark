import fitz
from wwc_TOC import isTOCPage
from utilities import annot_name
suffix="pages"

def get_colour(choice):
    # returns colour code for selection
    red = (1, 0, 0)
    orange = (1, 0.65, 0)
    yellow = (1, 1, 0.2)
    green = (0, 1, 0)
    blue = (0, 0, 1)
    indigo = (0.29, 0, 0.51)
    violet = (0.54, 0.17, 0.89)
    black = (0, 0, 0)
    colour = red  # default

    if choice == 'Red':
        colour = red
    if choice == 'Orange':
        colour = orange
    if choice == 'Yellow':
        colour = yellow
    if choice == 'Green':
        colour = green
    if choice == 'Blue':
        colour = blue
    if choice == 'Indigo':
        colour = indigo
    if choice == 'Violet':
        colour = violet
    if choice == 'Black':
        colour = black
    return colour

def paginate(doc, options, display=None, addHistory=True):

    fitz.TOOLS.set_annot_stem(annot_name+suffix)

    remove_pagination(doc, options, display, addHistory=False)

    if display:
        display.updatestatusBar("Adding pagination...")


    if options['pgRange']:
        pgRange=options['pgRange']
    else:
        pgRange=doc[0].get_label() + "-" + doc[doc.page_count-1].get_label()

    fontn = 'helv'
    if options['fontName'] == "Helvetica": fontn = 'helv'
    if options['fontName'] == 'Times Roman': font = 'TiRo'
    if options['fontName'] == "Courier": font = 'Cour'

    count = 0
    a=doc.parse_page_string(pgRange)

    if a:
        total = len(a)
        for pgNo in a:
            page=doc[pgNo]
            r = page.rect
            txt = page.get_label()
            if not isTOCPage(page):  # skip TOC pages
                width = fitz.getTextlength(txt, fontname="helv", fontsize=options['Size'])
                height = options['Size']

                top = r[1] + options['vMargin']*72
                bottom = r[3] - options['vMargin']*72
                left = r[0] + options['hMargin']*72
                right = r[2] - options['hMargin']*72
                hmiddle = left + (right - left) / 2
                vmiddle = top + (bottom-top)/2

                if options['VPOS'] == 'B':  # bottom
                    r[1] = bottom - height
                    r[3] = bottom
                if options['VPOS'] == 'M':  # middle
                    r[1] = vmiddle - height/2
                    r[3] = vmiddle + height/2
                if options['VPOS'] == 'T':  # top
                    r[1] = top
                    r[3] = top + height
                if options['HPOS'] == 'L':  # left
                    r[0] = left
                    r[2] = left + width
                if options['HPOS'] == 'C':  # centre
                    r[0] = hmiddle - (width / 2)
                    r[2] = hmiddle + (width / 2)
                if options['HPOS'] == 'R':  # right
                    r[0] = right - width
                    r[2] = right

                annot = page.addFreetextAnnot(rect=r * page.derotationMatrix, text=txt, fontname=fontn, fontsize=options['Size'],
                                              fill_color=None)
                annot.update(text_color=get_colour(options['Colour']), fill_color=None, rotate=page.rotation - 360)
                if display: display.dlist_tab[pgNo]=None
            count += 1
            percentComplete = int((float(count) / float(total)) * 100)
            if percentComplete % 10 == 0:
                if display: display.updateprogressBar(percentComplete)
        if display:
            display.updatestatusBar('Added pagination.')
            if addHistory: display.adddocHistory({'code':"DOC_paginated", 'options': options})

def isPaginated(doc):
    for page in doc:
        for annot in page.annots():
            info = annot.info
            id = info['id']
            if id.find(annot_name + suffix) > -1:
                return True
    return False

def remove_pagination(doc, options, display=None, addHistory=True):
    # delete annotations with names starting annot+suffix
    if not isPaginated(doc): return

    if display: display.updatestatusBar('Removing pagination...')

    if options['pgRange']:
        pgRange = options['pgRange']
    else:
        pgRange = doc[0].get_label() + "-" + doc[doc.page_count - 1].get_label()

    a = doc.parse_page_string(pgRange)
    count = 0
    total=len(a)
    if a:
        for pgNo in a:
            page=doc[pgNo]
            for annot in page.annots():
                info = annot.info
                id = info['id']
                if id.find(annot_name + suffix) > -1:
                    page.deleteAnnot(annot)
                    if display: display.dlist_tab[pgNo]=None
            count += 1
            percentComplete = int((float(count) / float(total)) * 100)
            if percentComplete % 10 == 0:
                if display: display.updateprogressBar(percentComplete)
        if display:
            display.updatestatusBar('Removed pagination.')
            if addHistory: display.adddocHistory({'code':"DOC_pagination_removed", 'options': options})






