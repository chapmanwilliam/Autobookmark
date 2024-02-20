import fitz  # pip install pymupdf
from pathlib import Path
from utilities import annot_name
from utilities import openFile, getUniqueFileName

from docx2pdf import convert
from pyxml2pdf import *

from wwc_page_labels import getpgLabelMapping
from wwc_named_destinations import pdf_get_named_destinations
import re
import os
from collections import OrderedDict

# from wwc_gui_config import updateprogressBar, updatestatusBar, errorMessage


open_trigger = "["  # if this appears at start of word, start hyperlinking what follows
close_trigger = "]"  # if this appears at end of word, stop hyperlinking
bHyperlinking = False  # flag that indicates when we are hyperlinking and when not
CPR = "https://www.justice.gov.uk/courts/procedure-rules/civil/rules/"
suffix = 'links'


def format_links(doc):
    red = (1.0, 0.0, 0.0)
    green = (0.0, 1.0, 0.0)

    border = {'width': 1.0, 'dashes': [], 'style': 'U'}

    internal_link_colors = {'stroke': red, 'fill': None}
    external_link_colors = {'stroke': green, 'fill': None}

    for page in doc:
        link = page.load_links()
        while link != None:
            if (link.is_external):
                link.set_border(border)
                link.set_colors(external_link_colors)
            else:
                link.set_border(border)
                link.set_colors(internal_link_colors)
            link = link.next


def getDictNamedDestinations(to_files):
    d = {}

    def Merge(dict1, dict2):
        res = {**dict1, **dict2}
        return res

    for f in to_files:
        doc = fitz.open(f)
        dict = pdf_get_named_destinations(
            doc)  # dict is dictionary of labels return tuple of pages, arr_labels is list of page labels in page order
        d = Merge(d, dict)
    return d


def getDictPageLabels(to_files):
    # we want to get from each to_file:
    # 1) whether to use prefix in the file name
    # 2) the page labels mapped to page numbers
    d = {}  # dictionary for page label mapping: {A3: {page_no: 4, 'file':file}}

    def Merge(dict1, dict2):
        res = {**dict1, **dict2}
        return res

    for f in to_files:
        doc = fitz.open(f)
        dict, arr_labels = getpgLabelMapping(
            doc)  # dict is dictionary of labels return tuple of pages, arr_labels is list of page labels in page order
        d = Merge(d, dict)
    return d


def remove_links(doc):
    count = 0
    total = doc.page_count
    for p in doc:  # iterate the document pages
        delete_links(p)
        count += 1
        percentComplete = int((float(count) / float(total)) * 100)


def hyperlink_(from_files, to_files):
    dictPgLbs = getDictPageLabels(to_files)  # get dictonary of references to pgLbs
    dictNmDt = getDictNamedDestinations(to_files)  # get dictionary of references to named destinations

    # TODO: perform checks if one reference appears more than once i.e. duplicate references
    def insert_named_destination(from_f, page, rect, m, d):
        file = os.path.relpath(d['file'], os.path.dirname(from_f))
        file = (Path(file).as_posix())
        l = {"kind": fitz.LINK_NAMED_R,
             "name": m,
             "from": rect,
             "file": file,
             "zoom": 'Fit',  # not needed, we accept the zoom of the destination
             "NewWindow": True
             }
        page.insert_link(l)

    def insert_page_destination(from_f, page, rect, p, d):
        file = os.path.relpath(d['file'], os.path.dirname(from_f))
        file = (Path(file).as_posix())
        l = {'kind': fitz.LINK_GOTOR,
             'from': rect,
             'to': fitz.Point(0, 0),
             'page': p,
             'file': file,
             'zoom': 'Fit',
             'NewWindow': True}
        page.insert_link(l)

    def convert_file_if_needed(from_f):
        if Path(from_f).suffix == '.doc' or Path(from_f).suffix == '.docx':
            convert(from_f, Path(from_f).with_suffix('.pdf'))
            doc = fitz.open(Path(from_f).with_suffix('.pdf'))
            return doc
        elif Path(from_f).suffix == '.opml':
            # TODO: convert from opml
            pass
        elif Path(from_f).suffix == '.pdf':
            doc = fitz.open(from_f)
            return doc
        else:
            print('Not an acceptable file')
            return None

    def link_this_doc(from_f):
        # check if word document: in which case convert to pdf first
        doc=convert_file_if_needed(from_f)
        if not doc: return

        for page in doc:  # TODO: what if references are to pages in the same file
            pattern = re.compile(
                r"\b[A-z]+\d+\b")  # matching pattern e.g. GP123 #TODO: is it necessary to filter the words like this?
            words = page.get_text("words", sort=True)
            matches = [w for w in words if pattern.match(w[4])]

            delete_links(page)  # remove our special links from this page

            for word in words:  # TODO: what if sequence of words matches named destination? Should we use triggers?
                # m = pattern.search(match[4]).group(0)
                m = word[4].rstrip('.:,;-()')  # remove trailing punctuation
                rect = fitz.Rect(word[0], word[1], word[2], word[3])
                if m in dictNmDt:
                    insert_named_destination(from_f, page, rect, m, dictNmDt[m])  # is it one of our named destinations
                    continue  # i.e. if we find a link to name destination, don't bother with page label
                if m in dictPgLbs:  # is it one of our page label references
                    p = dictPgLbs[m]['page'][0]  # use first of page references in case multiple
                    insert_page_destination(from_f, page, rect, p, dictPgLbs[m])

        format_links(doc)
        doc.saveIncr()
        doc.close()
        openFile(doc.name)

    for from_f in from_files:
        link_this_doc(from_f)


def hyperlink(doc):
    fitz.TOOLS.set_annot_stem(annot_name + suffix)

    page_range = '1-' + doc[doc.page_count - 1].get_label()  # default
    filename = doc.name

    p = Path.Path(filename).parents[0]
    n = Path.Path(filename).stem
    e = Path.Path(filename).suffix
    global bHyperlinking

    count = 0
    total = doc.page_count
    links = []
    #	for page in doc:
    for page in doc:  # iterate the document pages
        links.append(0)
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
                        if len(doc.get_page_numbers(pg_ref['word'])) > 0:
                            print("FOUND: " + pg_ref['word'])
                            l = {'kind': 1, 'from': fitz.Rect(pg_ref['rect']), type: 'goto',
                                 'page': doc.get_page_numbers(pg_ref['word'])[0], 'nflink': True, 'zoom': 0.0}
                            page.insertLink(l)

                    elif not pg_ref[
                                 'file'] == "":  # then we are going to page in another file: TODO: how to open in new window
                        filename = pg_ref['file']
                        filename = check_file_exists(filename, doc)
                        if not filename == "":
                            other_doc = fitz.open(filename)
                            if len(other_doc.get_page_numbers(pg_ref['word'])) > 0:
                                print("FOUND: " + pg_ref['word'])
                                l = {'kind': 5, 'from': fitz.Rect(pg_ref['rect']), type: 'goto',
                                     'page': other_doc.get_page_numbers(pg_ref['word'])[0], 'file': filename,
                                     'zoom': 0.0,
                                     'newWindow': True}
                                page.insertLink(l)
                            other_doc.close()
        # add_border_links(page)
        count += 1
        percentComplete = int((float(count) / float(total)) * 100)

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
    # deletes links with
    lnks = page.get_links()
    for lnk in lnks:
        id = lnk['id']
        print(id)
        # if id.find(annot_name+suffix)>-1:
        if 'fitz' in id: page.delete_link(lnk)


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
