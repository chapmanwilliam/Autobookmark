import fitz  # pip install pymupdf
import tkinter
from tkinter import font as tkFont
import pathlib as Path
from utilities import annot_name

from wwc_page_labels import getpgLabelMapping
import re
from collections import OrderedDict
#from wwc_gui_config import updateprogressBar, updatestatusBar, errorMessage


open_trigger = "["  # if this appears at start of word, start hyperlinking what follows
close_trigger = "]"  # if this appears at end of word, stop hyperlinking
bHyperlinking = False  # flag that indicates when we are hyperlinking and when not
CPR = "https://www.justice.gov.uk/courts/procedure-rules/civil/rules/"
suffix='links'

def remove_links(doc, display, options=None):
    display.updatestatusBar("Removing hyperlinking...")

    page_range = '1-' + doc[doc.pageCount-1].get_label() #default

    if options:
        if 'pgRange' in options:
            page_range = options['pgRange']
        if 'save' not in options:
            options['save'] = True
        if 'close' not in options:
            options['close'] = False
    else:
        options = {'save': True, 'close': True}
        page_range = '1-' + str(doc.pageCount)

    a = doc.parse_page_string(page_range)  # list of pages to consider
    if a:
        total=len(a)
        print(total)
        count=0
        for p in a:  # iterate the document pages
            page = doc[p]
            delete_links(page)
            count +=1
            percentComplete = int ((float(count) / float(total)) * 100)
            if percentComplete % 2 == 0: display.updateprogressBar(percentComplete)
            display.dlist_tab[p]=None
#        if options['save']: doc.saveIncr()
#        if options['close']: doc.close()
        display.displayPage()
    display.updatestatusBar('Finished deleting links.')




def hyperlink(doc, display, options=None):
    display.updatestatusBar("Starting hyperlinking...")
    fitz.TOOLS.set_annot_stem(annot_name+suffix)

    page_range = '1-' + doc[doc.pageCount-1].get_label() #default
    filename = doc.name

    if options:
        if 'pgRange' in options:
            page_range = options['pgRange']
        if 'save' not in options:
            options['save'] = False
        if 'close' not in options:
            options['close'] = False
    else:
        options = {'save': False, 'close': False}
        page_range = '1-' + str(doc.pageCount)

    p = Path.Path(filename).parents[0]
    n = Path.Path(filename).stem
    e = Path.Path(filename).suffix
    global bHyperlinking


    a = doc.parse_page_string(page_range)  # list of pages to consider

    if a:
        total=len(a)
        count=0
        links=[]
        #	for page in doc:
        for p in a:  # iterate the document pages
            links.append(0)
            page = doc[p]
            file_ciphers_flag = False
            if file_ciphers_flag is False:
                file_ciphers = get_file_ciphers(page, doc)  # search first page only for file ciphers
                file_ciphers_flag = True
            # delete links
            delete_links(page)
            for i in page.getText("words"):
                page_rect = page.bound()
                word_rect = fitz.Rect(i[0], i[1], i[2], i[3])
                pg_refs = []

                o, c = trigger(i[4])  # checks if [ at start or ] at end of word o=true means start, c=true means end

                if o:
                    bHyperlinking = True
                if bHyperlinking:
                    r = i[:4]
                    pg_refs = parse_word(r, i[4])
                if c:
                    bHyperlinking = False
                # hyperlink
                for pg_ref in pg_refs:
                    if not pg_ref['url'] == "":  # url link
                        l = {'kind': 2, 'from': fitz.Rect(pg_ref['rect']), type: 'uri', 'uri': pg_ref['url']}
                        page.insertLink(l)
                    else:  # reference to page in this or another file
                        if pg_ref['file'] == "":  # then we are going to page in this file
#                            if pg_ref['word'] in dict:
                            if len(doc.get_page_numbers(pg_ref['word']))>0:
                                print("FOUND: " + pg_ref['word'])
                                l = {'kind': 1, 'from': fitz.Rect(pg_ref['rect']), type: 'goto',
                                     'page': doc.get_page_numbers(pg_ref['word'])[0], 'nflink': True, 'zoom': 0.0}
                                page.insertLink(l)

                        elif not pg_ref[
                                     'file'] == "":  # then we are going to page in another file: TODO: how to open in new window
                            filename = pg_ref['file']
                            if filename in file_ciphers:  # if this is a cipher then use the cipher filename
                                filename = file_ciphers[filename]
                            print(filename)
                            filename = check_file_exists(filename, doc)
                            if not filename == "":
                                other_doc = fitz.open(filename)
                                if len(other_doc.get_page_numbers(pg_ref['word']))>0:
                                    print("FOUND: " + pg_ref['word'])
                                    l = {'kind': 5, 'from': fitz.Rect(pg_ref['rect']), type: 'goto',
                                         'page': other_doc.get_page_numbers(pg_ref['word'])[0], 'file': filename, 'zoom': 0.0,
                                         'newWindow': True}
                                    page.insertLink(l)
                                other_doc.close()
            page=doc.reload_page(page)
            display.dlist_tab[p]=None
            #add_border_links(page)
            count +=1
            percentComplete = int((float(count) / float(total)) * 100)
            if percentComplete % 2 == 0: display.updateprogressBar(percentComplete)

        # new_name=n + "_" + e
        # doc.save(p / new_name)
        #if options['save']: doc.saveIncr()
        #if options['close']: doc.close()
        display.displayPage()
    else:
        display.updatestatusBar('Error hyperlinking.')
        return False
    display.updatestatusBar('Finished hyperlinking.')
    return True


def get_file_ciphers(page, doc):
    # get blocks and search for "A"="filename.pdf"
    # returns dictionary

    dict = OrderedDict()
    for i in page.getText('blocks'):
        x = re.match(r"\"(.*)\"=\"(.*)\"", i[4], re.IGNORECASE)
        if x:  # i.e. a match
            cipher = x.group(1)
            filename = x.group(2)

            filename = check_file_exists(filename, doc)

            if not filename == "":    dict[cipher] = filename
            print(filename)
    return dict


def check_file_exists(filename, doc):
    # checks if filename exists
    # if not, try adding parent path
    # if that doesn't work return ''
    fpathdoc = Path.Path(doc.name)
    parent = fpathdoc.parent
    if Path.Path(filename).is_file():
        return filename
    else:
        # try adding parent of doc
        filename = parent / filename
        if Path.Path(filename).is_file():
            return filename
    return ""



def parse_word(r, word):
    # where r is the rect of the word
    # word might be[343]
    # word might be [23, 34, 34-35]
    # need to get proper rect for each part we want to hyperlink
    global whitebookfile
    widths = get_widths_each_character(word)
    width = r[2] - r[0]  # width of word

    # split word by ','
    pg_refs = []
    words1 = word.split(',')
    for w in words1:  # further split by -
        words2 = w.split('-')
        for x in words2:
            x = x.replace('[', "").replace(']', "")  # remove triggers
            if (len(x) > 0):
                f = ""
                url = ""
                fl = ""
                if x.find('/') > -1:
                    f = x.split('/')  # split by file ref
                    if f[0] == 'r':  # if this CPR reference
                        fl = ''
                        url = CPR + parse_cpr_ref(f[1])
                    else:  # this is simple page reference to another pdf
                        fl = f[0]
                    l = {'file': fl, "word": f[1], "rect": r, 'url': url}
                else:  # this is simple page reference to same pdf
                    l = {'file': "", "word": x, "rect": r, 'url': url}
                pg_refs.append(l)

    # now we need to set the rects for each page ref. That depends how far along the word it is
    for pg_ref in pg_refs:
        r1 = list(r)  # set new rect to word rect
        position = word.find(pg_ref['word'])
        l = len(pg_ref['word'])
        try:
            cum_w1 = widths[position]['cum_percent'] * width
            cum_w2 = widths[position + l]['cum_percent'] * width
            w = cum_w2 - cum_w1
            r1[0] = r1[0] + cum_w1
            r1[2] = r1[0] + w
            pg_ref['rect'] = r1
        except:
            return pg_refs

    return pg_refs


def parse_cpr_ref(cpr):
    # takes cpr and makes right url ending
    x = re.match("(\d+)\.(\d+(\w+)?)", cpr, re.IGNORECASE)  # search for rule
    s = ""
    if x:  # i.e. a match
        part = x.group(1)
        s = 'part' + part.zfill(2)
        if len(x.groups()) > 1:
            sub_part = x.group(0).lower()
            s = s + "#" + sub_part
    x = re.match("PD((\d)+\w+)(§((\d+)(\.\d+)?))?", cpr, re.IGNORECASE)  # search for Practice Direction
    if x:  # i.e. a match
        part1 = ""
        part2 = ""
        part3 = ""
        part1 = 'part' + x.group(2).zfill(2) + "/"
        part2 = 'pd_part' + x.group(1).zfill(3).lower()
        if len(x.groups()) > 3:
            part3 = "#" + x.group(4)
        s = part1 + part2 + part3

    return s


def get_width_text(txt, s=12, w='normal'):
    tkinter.Frame().destroy()
    f = tkFont.Font(family='Roman', size=s, weight=w)
    full_width = f.measure(txt)
    return full_width


def get_widths_each_character(txt, s=12, w='normal'):
    # returns array of width of each character
    # s=size of font
    tkinter.Frame().destroy()
    f = tkFont.Font(family='Roman', size=s, weight=w)
    full_width = f.measure(txt)
    ws = []
    cum_p = 0
    for c in txt:
        w = f.measure(c)
        p = w / full_width
        ws.append({'width': w, 'percent': p, 'cum_percent': cum_p})
        cum_p += p
    return ws


def delete_links(page):
    #deletes links with
    lnks = page.getLinks()
    for lnk in lnks:
        id=lnk['id']
        print(id)
        if id.find(annot_name+suffix)>-1:
            page.deleteLink(lnk)


def trigger(txt):
    # returns open if word begins with trigger or closed if word ends with trigger
    global open_trigger
    global close_trigger
    first_char = txt[0]
    last_char = txt[-1]
    o = False
    c = False
    if first_char == open_trigger:
        o = True
    if last_char == close_trigger:
        c = True
    return o, c


