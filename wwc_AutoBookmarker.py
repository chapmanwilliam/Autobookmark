from __future__ import absolute_import
from __future__ import print_function
import collections
import datetime
import os.path
from pathlib import Path
import re
import sys
from itertools import cycle
from typing import Dict

from wwc_parsebookmark import getdatefromText, getdatefromNode, gettextfromText, gettextpartDate, isValidDate, getdayofWeek

import fitz  # pip install pymupdf
import unidecode
import wwc_parser as dparser
from PyPDF2 import PdfReader
from PyPDF2.generic import AnnotationBuilder
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTChar
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, resolve1
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.psparser import PSLiteral
from six.moves import range
from treelib import Tree
from wwc_TOC import remove_square_brackets, write_chrono

# a.... 20/6/10   'assumes years <50 are 20??. So this is 20/6/2010
# b.... 20/6/2010
# c..... 6/10     'will translate this as 1/6/2010
# d..... 6/2010     'will translate this as 1/6/2010
# e..... 1 Jun 10   'will translate this as 1/6/2010	spaces can be replaced with '.' or '-' or '/'
# f..... 1 Jun 2010   'will translate this as 1/6/2010	  spaces can be replaced with '.' or '-' or '/'
# g..... Jun 10   'will translate this as 1/6/2010   spaces can be replaced with '.' or '-' or '/'
# h..... Jun 2010 'will translate this as 1/6/2010   spaces can be replaced with '.' or '-' or '/'
# i..... 2010     'will translate this as 1/1/2010   spaces can be replaced with '.' or '-' or '/'
# j..... 10     'will translate this as 1/1/2010     spaces can be replaced with '.' or '-' or '/'

patA = "((^|(,|( )|, ))(?P<day>\d{1,2})[\"\-\.](?P<month>\d{1,2})[\"\-\.](?P<year>\d{2}))"
patB = "((^|(,|( )|, ))(?P<day>\d{1,2})[\"\-\.\/](?P<month>\d{1,2})[\"\-\.\/](?P<year>\d{4}))"
patC = "((^|(,|( )|, ))(?P<month>\d{1,2})[\"\-\.](?P<year>\d{2}))"
patD = "((^|(,|( )|, ))(?P<month>\d{1,2})[\"\-\.](?P<year>\d{4}))"
patE = "((^|(,|( )|, ))(?P<day>\d{1,2})(st|nd|rd|th)?[\- \"\.]?(?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)[\- \"\.]?(?P<year>\d{1,2}))"
patF = "((^|(,|( )|, ))(?P<day>\d{1,2})(st|nd|rd|th)?[\- \"\.]?(?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)[\- \"\.]?(?P<year>\d{4}))"
patG = "((^|(,|( )|, ))(?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)[\- \"\.]?(?P<year>\d{2}))"
patH = "((^|(,|( )|, ))(?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)[\- \"\.]?(?P<year>\d{4}))"
patI = "((^|(,|( )|, ))(?P<year>\d{4}))"
patJ = "((^|(,|( )|, ))(?P<year>\d{2}))"
patK = "((?P<day>\d{1,2})(st|nd|rd|th)? *(?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December) *(?P<year>\d{4}) *(?P<hr>\d+):(?P<mm>\d+)(?P<AMPM>( *AM)|( *PM)|" ")?)"
patL = "((?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December) ?(?P<day>\d{1,2})(st|nd|rd|th)? ?(?P<year>\d{4}) *(?P<hr>\d+):(?P<mm>\d+)(?P<ss>(:\d\d)|" ")?(?P<AMPM>( ?AM)|( ?PM)|" ")?)"
patM = re.compile(
    r'(\b(?P<day>\d{1,2})(st|nd|rd|th)? *(?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December) *(?P<year>\d{4}) *(?P<hr>\d+):(?P<mm>\d+)(?P<AMPM>( *AM)|( *PM)|"")?)'
)
patN = re.compile(
    r'((?P<month>Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December) *(?P<day>\d{1,2})(st|nd|rd|th)? *(?P<year>\d{4}) *(?P<hr>\d+):(?P<mm>\d+)((?P<ss>:\d\d)|"")?(?P<AMPM>( *AM)|( *PM)|"")?)'
)

def_date = datetime.datetime(1066, 1, 1)
Chunk = collections.namedtuple("chunk", [
    "txt", "a", "size_chunk", "font_chunk", "font_size_chunk", "pg_size", "Dt",
    "Dt_txt"
])
Bookmark = collections.namedtuple("bookmark", ["txt", "Dt", "pg", "chunk"])

NO_PAGES = 0
percentComplete = 0
error_list = []
FILE = "../examples/Exhibits of correspondence.pdf"
KEY_WORDS = []
key_words_list = []
WP = {}  # dictionary of word properties
BOW = {}  # dictionary of words
MONTHS = {
    'JAN': 1,
    'JANUARY': 1,
    'FEB': 2,
    'FEBRUARY': 2,
    'MAR': 3,
    'MARCH': 3,
    'APR': 4,
    'APRIL': 4,
    'MAY': 5,
    'JUN': 6,
    'JUNE': 6,
    'JUL': 7,
    'JULY': 7,
    'AUG': 8,
    'AUGUST': 8,
    'SEP': 9,
    'SEPTEMBER': 9,
    'OCT': 10,
    'OCTOBER': 10,
    'NOV': 11,
    'NOVEMBER': 11,
    'DEC': 12,
    'DECEMBER': 12
}  # dictionary of months


class PdfMinerWrapper(object):
    """
    Usage:
    with PdfMinerWrapper('2009t.pdf') as doc:
        for page in doc:
           #do something with the page
    """

    def __init__(self, pdf_doc, pdf_pwd=""):
        self.pdf_doc = pdf_doc
        self.pdf_pwd = pdf_pwd
        self.no_pages = 0

    def __enter__(self):
        # open the pdf file
        self.fp = open(self.pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(self.fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument(parser, password=self.pdf_pwd)
        # connect the parser and document objects
        parser.set_document(doc)
        self.doc = doc
        return self

    def _parse_pages(self):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(char_margin=3.5, all_texts=True)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        count = 0
        for page in PDFPage.create_pages(self.doc):
            count += 1
            interpreter.process_page(page)
            # receive the LTPage object for this page
            layout = device.get_result()
            # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
            yield layout

    def __iter__(self):
        return iter(self._parse_pages())

    def __exit__(self, _type, value, traceback):
        self.fp.close()


def set_NO_PAGES(x):
    global NO_PAGES
    NO_PAGES = x


ESC_PAT = re.compile(r'[\000-\037&<>()"\042\047\134\177-\377]')


def e(s):
    return ESC_PAT.sub(lambda m: '&#%d;' % ord(m.group(0)), s)


def resolve_dest(dest, doc):  # unused
    if isinstance(dest, str):
        dest = resolve1(doc.get_dest(dest))
    elif isinstance(dest, PSLiteral):
        dest = resolve1(doc.get_dest(dest.name))
    if isinstance(dest, dict):
        dest = dest['D']
    return dest


def get_toc(filepath: str) -> Dict[int, str]:
    class TOCObject:
        def __init__(self, level, title, pageno, pagelabel):
            self.level = level
            self.title = title
            self.pageno = pageno
            self.pagelabel = pagelabel

    levels = {}
    ftree = Tree()
    ftree.create_node("Root", 0)  # root node
    levels[1] = 0
    old_level = 1
    count = 0
    with fitz.open(filepath) as doc:
        set_NO_PAGES(doc.page_count)
        t = doc.get_toc()
        for level, title, pageno in t:
            count += 1
            BkMk = TOCObject(level, title, pageno, pageno)
            if (level > old_level):
                levels[level] = count - 1
            ftree.create_node(title, count, parent=levels[level], data=BkMk)
            old_level = level

    #			print(level, title, pageno)
    def sorttree(node):
        return node.identifier

    #	print (ftree.show(key=sorttree,line_type='ascii'))
    return ftree


def get_next_level(BkMks, lvl, i):
    '''returns page of the next bookmark from i'th bookmark with same level'''
    pg = -1
    for x in range(i + 1, len(BkMks)):
        row = BkMks[x]
        level = row[0]
        page = row[2]
        if level <= lvl:
            pg = page
            return pg
    return NO_PAGES


def get_labels_each_page(f, f_name):
    return
    print("Getting labels for each page...")
    '''doc=slate.PDF(f)'''
    p = PdfReader(f)
    a = get_toc(f_name)
    # print(a)
    pages = []
    for z in range(0, NO_PAGES):
        empty_list = []
        pages.append(empty_list)

    for x in range(0, len(a)):
        row = a[x]
        level = row[0]
        text = re.sub(r'( )?\[(.|^\[|^\])*\]$', "", row[1])
        page = row[2]
        pg = get_next_level(a, level, x)
        for y in range(page, pg):
            pages[y].append(text)
    return pages


def get_text_each_page(fn, display=None, queue_to_gui=None, queue_from_gui=None, file_text=""):
    print("Getting text chunks each page...")
    if display: display.updatestatusBar("Getting text for each page....")
    if queue_to_gui: queue_to_gui.put('Getting pages....' + file_text)

    global percentComplete

    with PdfMinerWrapper(fn.name) as doc:
        count = 0
        chunks = []
        for x in range(0, NO_PAGES):
            empty_list = []
            chunks.append(empty_list)

        for page in doc:
            chunks_page = []
            print('Page no %d out of %d' % (page.pageid, NO_PAGES))
            percentComplete = (float(page.pageid) / float(NO_PAGES)) * 100
            if int(percentComplete) % 2 == 0 and display: display.updateprogressBar(percentComplete)
            if int(percentComplete) % 2 == 0 and queue_to_gui: queue_to_gui.put(str(int(percentComplete)))
            if not queue_from_gui.empty():
                if queue_from_gui.get() == u'Cancel': return None

            size = [int(page.width), int(page.height)]
            p = [page.pageid, NO_PAGES]
            chunks[count].append(p)
            chunks[count].append(size)
            BOW = {}  # new bag of words for this page
            for tbox in page:
                if not isinstance(tbox, LTTextBox):
                    continue
                # print ' '*1, 'Block', 'bbox=(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                # text_file.write("Block bbox %0.2f, %0.2f, %0.2f, %0.2f\n" % tbox.bbox)
                for obj in tbox:
                    # print ' '*2, obj.get_text().encode('UTF-8')[:-1], '(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                    text_chunk = unidecode.unidecode(obj.get_text())
                    size_chunk = obj.bbox
                    size_chunk = [int(x) for x in size_chunk]
                    for c in obj:
                        if not isinstance(c, LTChar):
                            continue
                        # print c.get_text().encode('UTF-8'), '(%0.2f, %0.2f, %0.2f, %0.2f)'% c.bbox, c.fontname, c.size,
                        font_chunk = c.fontname
                        font_size_chunk = int(c.size)
                        break
                    # print
                    l = get_location_on_page(get_left_of_square(size_chunk), size)
                    # print tidy_generally(text_chunk)
                    # print text_chunk
                    Dt, Dt_txt = dparser.parse(
                        text_chunk, fuzzy=True, dayfirst=True, yearfirst=False, default=def_date)
                    chunk = Chunk(text_chunk, l, size_chunk, font_chunk, font_size_chunk,
                                  size, Dt, Dt_txt)
                    AnalyzeChunk(chunk, BOW, KEY_WORDS)
                    # search for keywords
                    for key_word in KEY_WORDS:
                        if re.search(key_word, chunk.txt, re.IGNORECASE):
                            k = {
                                "keyword": key_word,
                                "chunk": chunk,
                                "pg": page.pageid - 1,
                                "Dt": None,
                                "Dt_txt": None
                            }
                            key_words_list.append(k)

                    chunks_page.append(chunk)
            chunks[count].append(chunks_page)
            chunks[count].append(BOW)
            count += 1

        return chunks

def get_text_each_pageQT(*args,**kwargs):
    print("Getting text chunks each page...")
    f_name=kwargs['f']
    file_stem=Path(f_name).stem

    fn=kwargs['fl']
    progress_callback=kwargs['progress_callback']
    pbar=kwargs['progress_bar']
    info_callback=kwargs['info_callback']
    info_callback.emit('Getting pages....' + file_stem,pbar)
    pbar=kwargs['progress_bar']

    global percentComplete
    no_pages=fn.page_count
    print(f'No pages doc {fn.page_count}')

    with PdfMinerWrapper(fn.name) as doc:
        count = 0
        chunks = []
        for x in range(0, no_pages):
            empty_list = []
            chunks.append(empty_list)

        for page in doc:
            chunks_page = []
            print('Page no %d out of %d' % (page.pageid, no_pages))
            percentComplete = (float(page.pageid) / float(no_pages)) * 100
            if int(percentComplete) % 2 == 0 and progress_callback: progress_callback.emit(int(percentComplete),pbar)

            size = [int(page.width), int(page.height)]
            p = [page.pageid, no_pages]
            chunks[count].append(p)
            chunks[count].append(size)
            BOW = {}  # new bag of words for this page
            for tbox in page:
                if not isinstance(tbox, LTTextBox):
                    continue
                # print ' '*1, 'Block', 'bbox=(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                # text_file.write("Block bbox %0.2f, %0.2f, %0.2f, %0.2f\n" % tbox.bbox)
                for obj in tbox:
                    # print ' '*2, obj.get_text().encode('UTF-8')[:-1], '(%0.2f, %0.2f, %0.2f, %0.2f)'% tbox.bbox
                    text_chunk = unidecode.unidecode(obj.get_text())
                    size_chunk = obj.bbox
                    size_chunk = [int(x) for x in size_chunk]
                    for c in obj:
                        if not isinstance(c, LTChar):
                            continue
                        # print c.get_text().encode('UTF-8'), '(%0.2f, %0.2f, %0.2f, %0.2f)'% c.bbox, c.fontname, c.size,
                        font_chunk = c.fontname
                        font_size_chunk = int(c.size)
                        break
                    # print
                    l = get_location_on_page(get_left_of_square(size_chunk), size)
                    # print tidy_generally(text_chunk)
                    # print text_chunk
                    Dt, Dt_txt = dparser.parse(
                        text_chunk, fuzzy=True, dayfirst=True, yearfirst=False, default=def_date)
                    chunk = Chunk(text_chunk, l, size_chunk, font_chunk, font_size_chunk,
                                  size, Dt, Dt_txt)
                    AnalyzeChunk(chunk, BOW, KEY_WORDS)
                    # search for keywords
                    for key_word in KEY_WORDS:
                        if re.search(key_word, chunk.txt, re.IGNORECASE):
                            k = {
                                "keyword": key_word,
                                "chunk": chunk,
                                "pg": page.pageid - 1,
                                "Dt": None,
                                "Dt_txt": None
                            }
                            key_words_list.append(k)

                    chunks_page.append(chunk)
            chunks[count].append(chunks_page)
            chunks[count].append(BOW)
            count += 1

        return chunks

def AnalyzeChunk(chunk, BOW, KEY_WORDS):
    # updates BagOfWords

    txt, loc, size, font, font_size, page_size, dt, dt_text = chunk

    # Dear
    if re.match('Dear', txt) and (l_in_ls(chunk, {1, 4, 7},
                                          'L')):  # i.e. Dear on the left side
        BOW['Dear'] = BOW.get('Dear', 0) + 1
    # Our ref
    if re.match('Our Ref', txt, re.IGNORECASE) and (l_in_ls(
            chunk, {7, 8, 9}, 'L')):  # i.e. Our ref at the top
        BOW['Our Ref'] = BOW.get('Our Ref', 0) + 1
    # Your ref
    if re.match('Your Ref', txt, re.IGNORECASE) and (l_in_ls(
            chunk, {7, 8, 9}, 'L')):  # i.e. Your ref at the top
        BOW['Your Ref'] = BOW.get('Your Ref', 0) + 1
    # From
    if re.match('From', txt) and (l_in_ls(chunk, {1, 4, 7},
                                          'L')):  # i.e. From on the left side
        BOW['From'] = BOW.get('From', 0) + 1
        if re.match('bold', font):  # extra point if in bold
            BOW['From'] = BOW.get('From', 0) + 1
    # To
    if re.match('To', txt) and (l_in_ls(chunk, {1, 4, 7},
                                        'L')):  # i.e. To on the left side
        BOW['To'] = BOW.get('To', 0) + 1
        if re.match('bold', font):  # extra point if in bold
            BOW['To'] = BOW.get('To', 0) + 1
    # Sent
    if re.match('Sent', txt) and (l_in_ls(chunk, {1, 4, 7},
                                          'L')):  # i.e. Sent on the left side
        BOW['Sent'] = BOW.get('Sent', 0) + 1
        if re.match('bold', font):  # extra point if in bold
            BOW['Sent'] = BOW.get('Sent', 0) + 1
    # Subject
    if re.match('Subject', txt) and (l_in_ls(
            chunk, {1, 4, 7}, 'L')):  # i.e. Subject on the left side
        BOW['Subject'] = BOW.get('Subject', 0) + 1
        if re.match('bold', font):  # extra point if in bold
            BOW['Subject'] = BOW.get('Subject', 0) + 1
    # Witness Statement
    if re.match('WITNESS STATEMENT', txt) and (l_in_ls(
            chunk, {2, 5, 8}, 'M')):  # i.e. Witness Statement in the middle
        BOW['Witness Statement'] = BOW.get('Witness Statement', 0) + 1

    if re.match('STATEMENT OF', txt) and (l_in_ls(
            chunk, {2, 5, 8}, 'M')):  # i.e. Witness Statement in the middle
        BOW['Witness Statement'] = BOW.get('Witness Statement', 0) + 1
    # File note
    if (re.match('FILE NOTE', txt) or re.match('File Note', txt)) and (l_in_ls(
            chunk, {7, 8, 9}, 'L')):  # i.e. File Note in top part
        BOW['File Note'] = BOW.get('File Note', 0) + 1
    # Conference note
    if (re.match('CONFERENCE NOTE', txt) or
        re.match('Conference Note', txt)) and (l_in_ls(
        chunk, {7, 8, 9}, 'L')):  # i.e. File Note in top part
        BOW['Conference Note'] = BOW.get('Conference Note', 0) + 1
    # Report
    if (re.search('REPORT', txt) or re.search('Report', txt)):  # i.e. Report
        BOW['Report'] = BOW.get('Report', 0) + 1
    # Consultant
    if (re.search(r"Consultant", txt, re.IGNORECASE)):  # i.e. a report Report
        BOW['Consultant'] = BOW.get('Consultant', 0) + 1
    # Instructions
    if (re.search(r"INSTRUCTIONS", txt) or
        re.search(r"BRIEF TO COUNSEL", txt)) and l_in_ls(
        chunk, {2, 5, 8}, 'M'):  # i.e. a instructions in the middle
        BOW['Instructions'] = BOW.get('Instructions', 0) + 1
    # Counsel
    if (re.search(r"COUNSEL", txt)):  # i.e. a Counsel
        BOW['Counsel'] = BOW.get('Counsel', 0) + 1

    # Index
    if (re.search(r"INDEX", txt) and
            (l_in_ls(chunk, {2, 5, 8}, 'M'))):  # i.e. INDEX on middle line
        BOW['Index'] = BOW.get('Index', 0) + 1

    # Claim Form
    if (re.search(r"Claim Form", txt) and (l_in_ls(chunk, {7, 8}, 'L')) and
            font_size > 15):
        BOW['Claim Form'] = BOW.get('Claim Form', 0) + 1

    # Notice of Funding
    if (re.search(r"Notice of funding", txt) and (l_in_ls(chunk, {7, 8}, 'L')) and
            font_size > 15):
        BOW['Notice of Funding'] = BOW.get('Notice of Funding', 0) + 1

    # Particulars of Claim
    if (re.search(r"PARTICULARS OF CLAIM", txt) and
            (l_in_ls(chunk, {5, 8}, 'M'))):
        BOW['POC'] = BOW.get('POC', 0) + 1

    # Schedule
    if (re.search(r"SCHEDULE", txt) and (l_in_ls(chunk, {5, 8}, 'M'))):
        BOW['Schedule'] = BOW.get('Schedule', 0) + 1
    if (re.search(r"Claimant", txt) and (l_in_ls(chunk, {6, 9}, 'R'))):
        BOW['Claimant'] = BOW.get('Claimant', 0) + 1
    if (re.search(r"Defendant", txt) and (l_in_ls(chunk, {6, 9}, 'R'))):
        BOW['Defendant'] = BOW.get('Defendant', 0) + 1

    # Defence
    if (re.search(r"DEFENCE", txt) and (l_in_ls(chunk, {5, 8}, 'M')) and
            font_size > 12):
        BOW['DEFENCE'] = BOW.get('DEFENCE', 0) + 1
    if (re.search(r"Defence", txt) and (l_in_ls(chunk, {7}, 'L'))):
        BOW['DEFENCE'] = BOW.get('DEFENCE', 0) + 1

    # DQ
    if (re.search(r"Directions questionnaire", txt) and
            (l_in_ls(chunk, {7}, 'L'))):
        BOW['DQ'] = BOW.get('DQ', 0) + 1
    # N181
    if (re.search(r"N181", txt) and (l_in_ls(chunk, {1, 2, 3}, 'L'))):
        BOW['N181'] = BOW.get('N181', 0) + 1

    # Notice of Trial Date
    if (re.search(r"Notice of Trial Date", txt) and (l_in_ls(chunk, {7}, 'L'))):
        BOW['Notice of Trial Date'] = BOW.get('Notice of Trial Date', 0) + 1

    # Notice of Allocation
    if (re.search(r"Notice of Allocation", txt) and (l_in_ls(chunk, {7}, 'L'))):
        BOW['Notice of Allocation'] = BOW.get('Notice of Allocation', 0) + 1

    # List
    if (re.search(r"List of [Dd]ocuments", txt) and (l_in_ls(chunk, {7}, 'L'))):
        BOW['List'] = BOW.get('List', 0) + 1

    # CNF
    if (re.search(r"Claim notification", txt) and (l_in_ls(chunk, {9}, 'L'))):
        BOW['CNF'] = BOW.get('CNF', 0) + 1
    if (re.search(r"formal claim", txt) and (l_in_ls(chunk, {7}, 'L'))):
        BOW['formal claim'] = BOW.get('formal claim', 0) + 1

    # Offer to Settle
    if (re.search(r"Offer to settle", txt) and (l_in_ls(chunk, {7}, 'L'))):
        BOW['Offer'] = BOW.get('Offer', 0) + 1

    # Order
    if (re.search(r"ORDER", txt) and (l_in_ls(chunk, {7, 8}, 'L'))):
        BOW['Order'] = BOW.get('Order', 0) + 1

    # CRU
    if (re.search(r"Compensation Recovery Unit", txt) and
            (l_in_ls(chunk, {9}, 'L'))):
        BOW['CRU'] = BOW.get('CRU', 0) + 1

    return BOW


def combine_labels_chunks():
    x = get_labels_each_page()
    y = get_text_each_page()
    if len(x) != len(y):
        print("Error: chunks and labels different sizes")
        return None
    i = 0
    for z in y:
        x[i].append(z)
        i += 1
    return x


def print_results(results):
    if results == None:
        return
    text_file = open("../Output/Results.txt", "w")
    '''prints for each page'''
    print(results, file=text_file)

    text_file.close()


def get_bookmarks_on_page(BkMks, pg):
    res = []
    for BkMk in BkMks:
        if BkMk.pg == pg:
            res.append(BkMk)
    return res


def get_middle_of_square(a):
    '''a is x1,y2,x2,y2'''
    mid_x = a[0] + ((a[2] - a[0]) / 2.0)
    mid_y = a[3] + ((a[3] - a[1]) / 2.0)
    mid_point = [mid_x, mid_y]
    return mid_point


def get_left_of_square(a):
    '''a is x1,y2,x2,y2'''
    l_x = a[0]
    mid_y = a[3] + ((a[3] - a[1]) / 2.0)
    l_point = [l_x, mid_y]
    return l_point


def get_right_of_square(a):
    '''a is x1,y2,x2,y2'''
    r_x = a[2]
    mid_y = a[3] + ((a[3] - a[1]) / 2.0)
    r_point = [r_x, mid_y]
    return r_point


def get_location_on_page(a, p):
    '''a is x,y
    p is dimensions of page x,y
    7 8 9
    4 5 6
    1 2 3
    '''
    x = a[0]
    y = a[1]

    left_third = p[0] * (1.0 / 3.0)
    mid_third = p[0] * (2.0 / 3.0)
    right_third = p[0] * (3.0 / 3.0)

    bottom_third = p[1] * (1.0 / 3.0)
    middle_third = p[1] * (2.0 / 3.0)
    top_third = p[1] * (3.0 / 3.0)

    x_part = 0
    y_part = 0
    if (x > 0):
        x_part = 0
    if (x > left_third):
        x_part = 1
    if (x > mid_third):
        x_part = 2

    if (y > 0):
        y_part = 0
    if (y > bottom_third):
        y_part = 1
    if (y > middle_third):
        y_part = 2

    result = (3 * y_part) + x_part + 1
    return result


def vertical_distance(chunk_a, chunk_b):
    # if chunk_a==None or chunk_b==None:
    #	return None
    # Height of b minus Height of a
    x1_a, y1_a, x2_a, y2_a = chunk_a.size_chunk
    x1_b, y1_b, x2_b, y2_b = chunk_b.size_chunk
    z = y1_b - y1_a
    return z


def get_distance_two_chunks(a, b):
    '''returns the distance between two chunk'''
    mid_a = get_middle_of_square(a.size_chunk)
    mid_b = get_middle_of_square(b.size_chunk)
    x1, y1 = mid_a[0], mid_a[1]
    x2, y2 = mid_b[0], mid_b[1]
    result = pow(pow((x2 - x1), 2) + pow((y2 - y1), 2), 0.5)
    return result


def is_left_aligned(a):
    '''a is a list of x,y pairs
    returns true if the pairs are left aligned within tolerance'''
    if len(a) <= 1:
        return None
    tolerance = 2
    x0 = c[0]
    flag = True
    for c in a:
        x = c[0]
        if abs(x - x0) > tolerance:
            flag = False
    return flag


def is_same_line(a):
    '''a is a list of chunks pairs
    returns true if the pairs are bottom aligned within tolerance'''
    if len(a) <= 1:
        return None
    tolerance = 2
    i_txt, i_loc, i_size, i_font, i_font_size, page_size, Dt, Dt_txt = a[0]
    y0 = i_size[1]
    flag = True
    for c in a:
        txt, loc, size, font, font_size, page_size, dt, dt_text = c
        x1 = size[0]
        y1 = size[1]
        x2 = size[2]
        y2 = size[3]
        # slope=(y2-y1)/(x2-x1)
        y = size[1]
        if abs(y - y0) > tolerance:
            flag = False
    return flag


def train():
    print_results(combine_labels_chunks())


def tidy_generally(txt):
    txt = re.sub(r' +', " ", txt)  # remove double spaces
    txt = txt.strip(' \n')  # strip leading and trailing spaces
    txt = txt.replace('\n', "")  # remove new line
    txt = txt.replace('\t', " ")  # remove tabs and replace with space
    txt = txt.replace("\'", "")  # remove '
    txt = re.sub(r'(\d) *: *(\d)', r"\1:\2",
                 txt)  # remove space(s) before and after colon and number
    return txt


def l_in_ls(chunk, list_of_locs, LMR):
    # returns true if loc is found in list of locs
    # loc is location on the page
    loc = 0
    txt, loc, size, font, font_size, page_size, dt, dt_text = chunk
    if LMR == 'L':
        loc = get_location_on_page(get_left_of_square(size), page_size)
    if LMR == 'M':
        loc = get_location_on_page(get_middle_of_square(size), page_size)
    if LMR == 'R':
        loc = get_location_on_page(get_right_of_square(size), page_size)
    if loc == 0:
        return False

    for l in list_of_locs:
        if l == loc:
            return True
    return False


def isthere(x, chunks, bold=False, list_of_locs=None, LMR='L'):
    '''returns list of chunks containing x on page with flags for bold and position'''
    '''x is list of key words'''
    res = []
    for chunk in chunks:
        txt, loc, size, font, font_size, page_size, dt, dt_text = chunk
        if re.search(x, txt) and (bold == False or re.search("Bold", font)) and (
                list_of_locs == None or l_in_ls(chunk, list_of_locs, LMR)):
            res.append(chunk)

    return res


def get_right_bit(this_chunk, chunks):
    right_bit = ""
    if this_chunk == None:
        return ""

    for chunk in chunks:
        txt, loc, size, font, font_size, page_size, dt, dt_text = chunk
        if is_same_line([this_chunk, chunk]):
            right_bit += txt.strip(' \n')
    return right_bit


def tidy_right_bit_from(txt):
    txt = re.sub(r'From:?', "", txt)  # remove from
    txt = tidy_generally(txt)
    txt = re.sub(r'-+', '-', txt)

    new_txt = ""  # default

    names_list = []

    addressees = txt.split(";")  # split by ;

    for addressee in addressees:
        # emails are '< >' or '[]'
        # print addressee
        emails = re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', addressee,
                           re.IGNORECASE)  # extract emails
        if emails:
            addressee = re.sub(
                r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
                "",
                addressee,
                flags=re.IGNORECASE)  # remove email from
            addressee = re.sub(
                r'[\<\[].*[\]\>]', "", addressee, flags=re.IGNORECASE)  # remove email from
            addressee = tidy_generally(addressee)
        # print addressee

        names = re.search(r'[\w\.\-\_ \@]+', addressee,
                          re.IGNORECASE)  # names in right order
        names_ = re.search(r'[\w\.\-\_\@]+, [\w\.\-\_]+', addressee,
                           re.IGNORECASE)  # names back to front
        if names_:
            s = names_.group().split(",")
            a = s[1] + " " + s[0]  # reverse the names to put christian name first
            names_list.append(a)
            continue
        if names:
            names_list.append(names.group())
            continue
        if emails:
            names_list.append(emails.group())
            continue

    new_txt = ", ".join(names_list)
    new_txt = tidy_generally(new_txt)
    return new_txt


def tidy_right_bit_to(txt):
    txt = re.sub(r'To:?', "", txt)  # remove To
    txt = tidy_generally(txt)
    txt = re.sub(r'-+', '-', txt)

    new_txt = ""  # default

    names_list = []

    addressees = txt.split(";")  # split by ;

    for addressee in addressees:
        emails = re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', addressee,
                           re.IGNORECASE)  # extract emails
        if emails:
            addressee = re.sub(
                r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
                "",
                addressee,
                flags=re.IGNORECASE)  # remove email from
            addressee = re.sub(
                r'[\<\[].*[\]\>]', "", addressee, flags=re.IGNORECASE)  # remove email from
            addressee = tidy_generally(addressee)

        names = re.search(r'[\w\.\-\_ \@]+', addressee,
                          re.IGNORECASE)  # names in right order
        names_ = re.search(r'[\w\.\-\_\@]+, [\w\.\-\_]+', addressee,
                           re.IGNORECASE)  # names back to front
        if names_:
            s = names_.group().split(",")
            a = s[1] + " " + s[0]  # reverse the names to put christian name first
            names_list.append(a)
            continue
        if names:
            names_list.append(names.group())
            continue
        if emails:
            names_list.append(emails.group())
            continue

    new_txt = ", ".join(names_list)
    new_txt = tidy_generally(new_txt)
    return new_txt


def get_chunks_with_dates_no_DOB(chunks):
    '''returns list of chunks with dates excluding ones that suggest this is date of birth'''
    list_dates = []
    for chunk in chunks:
        if chunk.Dt and (re.search(r'DOB', chunk.txt) is None and
                         re.search(r'd.o.b.', chunk.txt) is None):
            list_dates.append(chunk)
    return list_dates


def get_chunks_with_dates(chunks):
    '''returns list of chunks with dates'''
    list_dates = []
    for chunk in chunks:
        if chunk.Dt:
            list_dates.append(chunk)
    return list_dates


def get_date_from_chunk_(chunk):
    # returns datetime object if there is a date in this chunk; else None
    if chunk == None:
        return None
    txt, loc, size, font, font_size, page_size, dt, dt_text = chunk
    txt = re.sub(r' +', " ", txt)  # remove double spaces
    txt = re.sub(r'(\d) (\d)', r"\1\2", txt)  # remove space between digits
    txt = re.sub(r',', "", txt)  # remove commas
    # result=re.search(patB,txt) or re.search(patF,txt)
    if dt: return dt
    '''
    result=True
    if result:
        #txt=result.group(0)
        try:
            d,y=dparser.parse(txt, fuzzy=True, dayfirst=True, default=def_date)
            if d:
                return d
        except:
            print "Not parsed from date_chunk: " + txt
    '''
    return None


def get_date_text_from_date_object(Dt):
    # returns text dd/mm/yyyy from Dt object
    if Dt == None:
        return ""
    return str(Dt.day) + "/" + str(Dt.month) + "/" + str(Dt.year)


def get_date_from_chunk(chunk):
    date_txt = ""
    if chunk == None:
        return ""
    txt, loc, size, font, font_size, page_size, dt, dt_text = chunk
    txt = re.sub(r' +', " ", txt)  # remove double spaces
    # txt=re.sub(r'(\d) (\d)',r"\1\2",txt) #remove space between digits
    txt = re.sub(r',', "", txt)  # remove commas
    result = re.search(patB, txt)
    date_txt = ""
    if result:
        dd = int(result.group('day'))
        mm = int(result.group('month'))
        yy = int(result.group('year'))
        date_txt = format(dd, '02') + "/" + format(mm, '02') + "/" + format(yy, '04')
    result = re.search(patF, txt)
    if result:
        dd = int(result.group('day'))
        mm = int(MONTHS[result.group('month').upper()])
        yy = int(result.group('year'))
        date_txt = format(dd, '02') + "/" + format(mm, '02') + "/" + format(yy, '04')

    return date_txt


def get_distance_from_top_page(chunk):
    # returns the distance from the top of the page
    if chunk is None: return None
    x2_p, y2_p = chunk.pg_size
    x1_c, y1_c, x2_c, y2_c = chunk.size_chunk
    distance_from_top = y2_p - y2_c
    return distance_from_top


def get_most_n_chunk(chunks):
    # returns most northerly chunk
    if len(chunks) == 0:
        return None
    x = 10000
    # pg, size_page, chunks_whole_page, BOW=page
    y = 10000
    comp_chunk = Chunk("", 9, [x, y, x, y], "", 11, [600, 845], None,
                       None)  # i.e. a chunk in further ne corner

    res = chunks[0]
    for chunk in chunks:
        z = abs(vertical_distance(comp_chunk, chunk))
        if z < x:
            x = z
            res = chunk
    return res


def get_most_n_date(chunks):
    return get_most_n_chunk(get_chunks_with_dates(chunks))


def get_most_ne_chunk(chunks):
    # returns most north-easterly chunk on the page
    if len(chunks) == 0:
        return None
    x = 10000
    y = 10000
    comp_chunk = ["", 9, [x, y, x, y], "", 11,
                  [600, 845]]  # i.e. a chunk in further ne corner

    res = chunks[0]
    for chunk in chunks:
        z = get_distance_two_chunks(comp_chunk, chunk)
        if z < x:
            x = z
            res = chunk
    return res


def get_nearest_chunk(chunk, chunks):
    # returns nearest chunk in chunks to chunk
    '''arbitrarily high no'''
    x = 10000
    n_c = None
    for c in chunks:
        d = get_distance_two_chunks(c, chunk)
        if d < x:
            x = d
            n_c = c
    return n_c


def get_nearest_vertical_chunk(chunk, chunks):
    x = 10000
    n_c = None
    for c in chunks:
        d = abs(vertical_distance(c, chunk))
        if d < x:
            x = d
            n_c = c
    return n_c


def get_nearest_chunk_within_x_lines(chunk, chunks, x=5):
    # returns nearest chunk if it is within x lines of chunk
    # else returns None
    if chunk is None or chunks is None:
        print("Shouldn't get here: null parameters passed to get nearest chunk")
        return None

    nearest_chunk = get_nearest_vertical_chunk(chunk, chunks)
    print("Nearest vertical chunk: ", nearest_chunk)
    if nearest_chunk is None:
        print("Shouldn't get here: couldn't find nearest chunk")
        return None

    z = abs(vertical_distance(chunk, nearest_chunk))
    x1_a, y1_a, x2_a, y2_a = chunk.size_chunk
    height_of_chunk = y2_a - y1_a
    no_lines = round(float(z) / float(height_of_chunk))
    if no_lines <= x:
        return nearest_chunk
    else:
        return None
    return None


def get_chunks_same_line(chunk, chunks):
    # returns chunks on same line
    chunks_same_line = []
    if chunk is None or chunks is None:
        return None
    # txt,loc,size,font,font_size, page_size, dt, dt_text=chunk

    ya = chunk.size_chunk[1]

    tolerance = 2

    for c in chunks:
        # txt1, loc1, size1, font1, font_size1, page_size1=c
        yb = c.size_chunk[1]
        if abs(yb - ya) <= tolerance:
            chunks_same_line.append(c)

    return chunks_same_line


def get_txt_date_from_email_(chunk):
    if chunk == None:
        return ""
    txt, loc, size, font, font_size, page_size, dt, dt_text = chunk
    try:
        r = dparser.parse(txt, fuzzy=True, default=def_date)
        y = str(r.year)
        m = str(r.month)
        d = str(r.day)
        hh = str(r.hour)
        mm = str(r.minute)
        ss = str(r.second)
        result = "(" + hh + mm + "), " + d + "/" + m + "/" + y
    except ValueError as e:
        print(txt)
    return result


def get_txt_date_from_email(chunk):
    if chunk == None:
        return ""
    txt, loc, size, font, font_size, page_size, dt, dt_text = chunk
    txt = tidy_generally(txt)
    txt = re.sub(r',', "", txt)  # remove commas
    txt = re.sub(r'at ', "", txt)  # remove at
    new_text = ""

    if patM.search(txt):
        parts = patM.search(txt)
        dd = format(int(parts.group('day')), '02')
        mmmm = format(MONTHS[parts.group('month').upper()], '02')
        yyyy = format(int(parts.group('year')), '04')
        hh_n = int(parts.group('hr'))
        mm = format(int(parts.group('mm')), '02')

        AM_PM = ""
        if parts.group('AMPM') != None:
            AM_PM = parts.group('AMPM')
        if "PM" in AM_PM and hh_n < 12:
            hh_n += 12
        hh = "{:0>2}".format(hh_n)
        new_text = "(" + hh + mm + "), " + dd + "/" + mmmm + "/" + yyyy

    if patN.search(txt):
        parts = patN.search(txt)
        dd = format(int(parts.group('day')), '02')
        mmmm = format(MONTHS[parts.group('month').upper()], '02')
        yyyy = format(int(parts.group('year')), '04')
        hh_n = int(parts.group('hr'))
        mm = format(int(parts.group('mm')), '02')

        AM_PM = ""
        ss = ""
        if parts.group('AMPM') != None:
            AM_PM = parts.group('AMPM')
        if "PM" in AM_PM and hh_n < 12:
            hh_n += 12
        hh = "{:0>2}".format(hh_n)
        if parts.group('ss') != None:
            ss = parts.group('ss')

        new_text = "(" + hh + mm + ss + "), " + dd + "/" + mmmm + "/" + yyyy

    new_text = new_text.strip()

    return new_text


def do_letter_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is letter
    pg, size_page, chunks, BOW = page
    dear = get_most_n_chunk(isthere('Dear', chunks, False, {1, 4, 7},
                                    'L'))  # get Dear chunk
    res = get_most_n_chunk(get_chunks_with_dates_no_DOB(chunks))
    print("Letter Page: ", pg)
    date_txt = ""
    Dt = None
    if dear != None and res != None:
        if vertical_distance(dear,
                             res) > 0:  # check date chunk is higher than dear chunk
            Dt = res.Dt
            date_txt = res.Dt_txt
    txt = "Letter" + date_txt
    BkMk = Bookmark(txt, Dt, pg[0] - 1, res)
    Lts.append(BkMk)
    return


def do_email_this_page(page, nextpage, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is email
    pg, size_page, chunks, BOW = page
    npg, nsize_page, nchunks, nBOW = nextpage

    print("Email Page: ", pg)
    fr = isthere('From', chunks, False, {1, 4, 7}, 'L')
    for each_fr in fr:  # for each chunk that has a "From"
        f_txt = tidy_right_bit_from(get_right_bit(each_fr, chunks))
        print("Chunks with dates: ", get_chunks_with_dates(chunks))
        n_chunk = get_nearest_chunk_within_x_lines(each_fr,
                                                   get_chunks_with_dates(chunks), 8)
        print("Nearest chunk with date: ", n_chunk)
        Dt, date_txt = None, None
        if n_chunk:
            Dt = n_chunk.Dt
            date_txt = n_chunk.Dt_txt

        if date_txt is None:  # have a look on next page
            Sn = isthere('Sent', chunks, False, {1, 4, 7}, 'L')
            n_chunk = get_most_n_chunk(get_chunks_with_dates(Sn))
            if n_chunk:
                date_txt = n_chunk.Dt_txt

        if date_txt is None:
            date_txt = ""

        to_txt = tidy_right_bit_to(
            get_right_bit(
                get_nearest_chunk_within_x_lines(
                    each_fr, isthere("To", chunks, False, {1, 4, 7}, 'L')), chunks))
        if to_txt == "":  # have a look on next page
            to_txt = tidy_right_bit_to(
                get_right_bit(
                    get_most_n_chunk(isthere("To", nchunks, False, {7}, 'L')), nchunks))

        txt = 'Email ' + f_txt + ' to ' + to_txt + date_txt
        if each_fr != None:
            BkMk = Bookmark(txt, Dt, pg[0] - 1, n_chunk)
            Lts.append(BkMk)
    return


def do_instructions_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is instructions
    pg, size_page, chunks, BOW = page
    print("Instructions: ", pg)
    txt = "Instructions"
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_witness_statement_this_page(page, input, output, Lts):
    pg, size_page, chunks, BOW = page
    print("Witness Statement: ", pg)
    # get the name of the witness
    # Either:
    # - 'WITNESS STATEMENT OF JACKIE BOACHIE'
    # - 'I, JACKIE BOACHIE'
    # - 'NAME OF WITNESS: JACKIE BOACHIE'
    # - 'STATEMENT OF JACKIE BOACHIE'

    # 1
    l_chunks = isthere("WITNESS STATEMENT", chunks, False, {2, 5, 8}, 'M')
    name = ""
    for l_chunk in l_chunks:
        txt, loc, size, font, font_size, page_size, dt, dt_text = l_chunk
        s = re.search(r"\bWITNESS STATEMENT( +OF)?(?P<name>( +[A-Z]\w+\b){1,3})",
                      txt)
        if s:
            name = s.group("name").title().replace(r'  +', " ")
            break
    # 2
    if name == "":
        l_chunks = isthere("I, ", chunks)
        for l_chunk in l_chunks:
            txt, loc, size, font, font_size, page_size, dt, dt_text = l_chunk
            s = re.search(r"\b[I|],(?P<name>( +[A-Z]\w+\b){1,3})", txt)
            if s:
                name = s.group("name").title().replace(r'  +', " ")
                break
    # 3
    if name == "":
        l_chunks = isthere("STATEMENT OF", chunks, False, {2, 5, 8})
        for l_chunk in l_chunks:
            txt, loc, size, font, font_size, page_size, dt, dt_text = l_chunk
            s = re.search(r"\bSTATEMENT( +OF)?(?P<name>( +[A-Z]\w+\b){1,3})", txt)
            if s:
                name = s.group("name").title().replace(r'  +', " ")
                break

    txt = "w/s" + name
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_file_note_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("File note: ", pg)

    Dt_txt = ""
    Dt = get_chunks_same_line(
        get_most_n_chunk(
            isthere('Date', chunks, False, {1, 4, 7}) + isthere('DATE', chunks, False,
                                                                {1, 4, 7})), chunks)
    if Dt:
        for D in Dt:  # iterate chunks on same line and look for date
            test = get_date_from_chunk_(D)
            if D.Dt is not None:
                Dt_txt = D.Dt_txt

    txt = "File Note" + Dt_txt
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_conference_note_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Conference note: ", pg)

    Dt_txt = ""
    Dt = get_chunks_same_line(
        get_most_n_chunk(
            isthere('Date', chunks, False, {1, 4, 7}) + isthere('DATE', chunks, False,
                                                                {1, 4, 7})), chunks)

    if Dt:
        for D in Dt:  # iterate chunks on same line and look for date
            # test=get_date_from_chunk_(D)
            if D.Dt:
                Dt_txt = D.Dt_txt

    txt = "Conference Note" + Dt_txt
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_index_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Index: ", pg)
    txt = "Index"
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_claim_form_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Claim Form: ", pg)
    n_chunk = get_most_n_date(chunks)
    Dt = None
    Dt_txt = ""
    if n_chunk:
        Dt = n_chunk.Dt
        Dt_txt = n_chunk.Dt_txt
    txt = "Claim Form" + Dt_txt
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_notice_of_funding_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is notice of funding
    pg, size_page, chunks, BOW = page
    print("Notice of Funding: ", pg)
    n_chunk = get_most_n_date(chunks)
    Dt = None
    Dt_txt = ""
    if n_chunk:
        Dt = n_chunk.Dt
        Dt_txt = n_chunk.Dt_txt
    txt = "Notice of Funding, " + Dt_txt
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_poc_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("POC: ", pg)
    txt = "Particulars of Claim"
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_schedule_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Schedule: ", pg)
    txt = "Schedule"
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_D_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("D: ", pg)
    txt = "Defence"
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_DQ_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("DQ: ", pg)
    txt = "DQ"
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_LIST_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("LIST: ", pg)
    txt = "List"
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_NTD_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Notice of Trial Date: ", pg)
    n_chunk = get_most_n_date(chunks)
    Dt = n_chunk.Dt
    Dt_txt = n_chunk.Dt_txt
    txt = "Notice of Trial Date, " + Dt_txt
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_NAC_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Notice of Allocation: ", pg)
    n_chunk = get_most_n_date(chunks)
    Dt = n_chunk.Dt
    Dt_txt = n_chunk.Dt_txt
    txt = "Notice of Allocation, " + Dt_txt
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_CNF_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("CNF: ", pg)
    txt = "CNF, "
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_offer_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Offer: ", pg)
    txt = "Offer, "
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_order_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("Order: ", pg)
    txt = "Order, "
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def do_CRU_this_page(page, input, output, Lts):
    # processes this page (and the next if necessary) assuming it is file note
    pg, size_page, chunks, BOW = page
    print("CRU: ", pg)
    n_chunk = get_most_n_date(chunks)
    Dt = None
    Dt_txt = ""
    if n_chunk:
        Dt = n_chunk.Dt
        Dt_txt = n_chunk.Dt_txt
    txt = "CRU, " + Dt_txt
    output.add_outline_item(txt, pg[0] - 1, parent=None)  # add bookmark
    return txt, pg[0] - 1


def categorise_page(page):
    pg, size_page, chunks, BOW = page
    # Score From, To, Sent, Subject
    # print BOW
    email_score = BOW.get('From', 0) + BOW.get('To', 0) + BOW.get(
        'Sent', 0) + BOW.get('Subject', 0)
    letter_score = 0
    if BOW.get('Dear', 0) > 0:
        letter_score = 3 * BOW.get('Dear', 0) + BOW.get('Our Ref', 0) + BOW.get(
            'Your Ref', 0)
    instruction_score = 2 * BOW.get('Instructions', 0) + BOW.get('Counsel', 0)
    witness_statement = 0
    if BOW.get('Witness Statement', 0) > 0:
        witness_statement += (3 * BOW.get('Witness Statement', 0) + BOW.get(
            'Claimant', 0) + BOW.get('Defendant', 0))

    file_note = BOW.get('File Note', 0)
    conference_note = BOW.get('Conference Note', 0)
    index = BOW.get('Index', 0)
    claim_form = BOW.get('Claim Form', 0)
    POC = BOW.get('POC', 0)
    DQ = BOW.get('DQ', 0)
    NTD = BOW.get('Notice of Trial Date', 0)
    D = BOW.get('DEFENCE', 0)
    NAC = BOW.get('Notice of Allocation', 0)
    LIST = BOW.get('List', 0)
    CNF = BOW.get('CNF', 0) + BOW.get('formal claim', 0)
    Offer = BOW.get('Offer', 0)
    Order = BOW.get('Order', 0)
    CRU = BOW.get('CRU', 0)
    Schedule = 0
    if BOW.get('Schedule', 0) > 0:
        # Schedule=BOW.get('Schedule',0)
        Schedule += (3 * BOW.get('Schedule', 0) + BOW.get('Claimant', 0) + BOW.get(
            'Defendant', 0))
    print(Schedule)
    NoticeOfFunding = BOW.get('Notice of Funding', 0)

    if email_score > 2:
        return 1  # return as for email
    if letter_score > email_score:
        return 2  # return as for letter
    if instruction_score > 2:
        return 3  # return as for instruction
    if witness_statement > 3:
        return 4  # return as for witness statement
    if file_note > 0:
        return 5  # return as for file note
    if index > 0:
        return 6  # return as for index
    if claim_form > 0:
        return 7  # return as for claim form
    if POC > 0:
        return 8  # return as for POC
    if DQ > 0:
        return 9  # return as for DQ
    if NTD > 0:
        return 10  # return as for DQ
    if D > 0:
        return 11  # return as for D
    if NAC > 0:
        return 12  # return as for NAC
    if LIST > 0:
        return 13  # return as for LIST
    if CNF > 1:
        return 14  # return as for CNF
    if Offer > 0:
        return 15  # return as for offer
    if Order > 0:
        return 16  # return as for order
    if CRU > 0:
        return 17  # return as for CRU
    if Schedule > 3:
        return 18  # return as for Schedule
    if conference_note > 0:
        return 19  # return as for file note
    if NoticeOfFunding > 0:
        return 20

    return 0


def date_scrape(page, input, output, Dts, date_parent=None):
    pg, size_page, chunks, BOW = page
    print("Date scraping: ", pg)
    chunks_dates = get_chunks_with_dates(chunks)
    for chunk in chunks_dates:
        Dt = chunk.Dt
        Dt_txt = chunk.Dt_txt
        txt = "Date" + Dt_txt
        BkMk = Bookmark(txt, Dt, pg[0] - 1, chunk)
        Dts.append(BkMk)
    return


def paste_dates(output, Dts, date_parent=None):
    parent = date_parent
    old_y = 0
    y = 0
    for Dt in Dts:
        if Dt.Dt:
            y = Dt.Dt.year
            if (old_y != y):
                parent = output.add_outline_item(str(y), Dt.pg, date_parent)
            output.add_outline_item(Dt.txt, Dt.pg, parent)
            if Dt.chunk:
                output.addLink(
                    Dt.pg, Dt.pg, Dt.chunk.size_chunk, border=[10, 1, 1])  # add a link
        old_y = y


def paste_letters(output, Lts, toc, doc, letter_parent=None):
    parent = letter_parent
    old_email = ""
    for Lt in Lts:
        if re.search("Email", Lt.txt):
            if old_email != Lt.txt:
                output.add_outline_item(Lt.txt, Lt.pg, letter_parent)
                toc.append([2, Lt.txt, Lt.pg + 1])
        else:
            output.add_outline_item(Lt.txt, Lt.pg, letter_parent)
            toc.append([2, Lt.txt, Lt.pg + 1])
        if Lt.chunk:
            # Add the line
            annotation = AnnotationBuilder.link(
                rect=Lt.chunk.size_chunk,
                target_page_index=Lt.pg,
            )
            output.add_annotation(
                Lt.pg, annotation=annotation)  # add a link
        #            print(Lt.chunk.size_chunk)
        #            p1=fitz.Point(Lt.chunk.size_chunk[0],Lt.chunk.size_chunk[1])
        #            p2=fitz.Point(Lt.chunk.size_chunk[2],Lt.chunk.size_chunk[1])
        #            doc[Lt.pg].addLineAnnot(p1,p2)

        old_email = Lt.txt


def paste_key_words(output, Ks, key_words_parent=None):
    for k in Ks:
        if k['Dt']:
            txt = k['keyword'] + k['Dt_txt']
        else:
            txt = k['keyword']
        output.add_outline_item(txt, k['pg'], key_words_parent)
        if k['chunk']:
            output.addLink(
                k['pg'], k['pg'], k['chunk'].size_chunk, border=[1, 10, 1])  # add a link


def do(f_name, doc, display=None, queue_to_gui=None, queue_from_gui=None, file_text=""):
    # app=wx.App(False)
    # frame=wx.Frame(None,wx.ID_ANY,"AutoBookmarker")
    # frame.Show(True)
    # app.MainLoop()
    # f_name=f_name.encode('string-escape')
    # f_name = f_name.replace("\\", "\\\\")
    # print f_name
    other_toc = []
    if os.path.isfile(f_name) == False:
        print("O: file not found.")
        print(f_name)
        return
    with open(f_name, 'rb') as fn:
        ftree = get_toc(f_name)  # tree
        # get_labels_each_page(fn, f_name)
        pages = get_text_each_page(fn, display, queue_to_gui,queue_from_gui, file_text)
        if pages is None: return
        if display:
            display.updatestatusBar('Creating bookmarks...')
        if queue_to_gui:  queue_to_gui.put('Bookmarks...' + file_text)
        from PyPDF2 import PdfWriter, PdfReader

        output = PdfWriter()  # open output
        input = PdfReader(fn)  # open input
        output.page_mode = "/UseOutlines"

        running = True
        licycle = cycle(pages)
        page = nextpage = next(licycle)
        count = 0
        no_matches = 0
        no_blank_pages = 0
        blank_pages = []

        Dts = []
        Lts = []
        total = len(pages)
        while count < len(pages):
            count += 1
            page, nextpage = nextpage, next(licycle)
            pg, size_page, chunks, BOW = page

            p = input.pages[pg[0] - 1]
            if not queue_from_gui.empty():
                if queue_from_gui.get() == u'Cancel': return None


            #print("No chunks: %d" % len(chunks))
            percentComplete = (float(count) / float(total)) * 100
            if int(percentComplete) % 2 == 0 and display: display.updateprogressBar(percentComplete)
            if int(percentComplete) % 2 == 0 and queue_to_gui:
                queue_to_gui.put(str(int(percentComplete)))

            if True:
                output.add_page(p)  # insert page
                # if p.getContents():
                #	print p.getContents()['/Filter']
                # else:
                #	print "No contents"

                # add bookmark for dates
                if count == 1:
                    # blank_parent = output.add_outline_item("Blanks", 0, parent=None)  # add bookmark
                    # date_parent = output.add_outline_item("Dates", 0, parent=None)  # add bookmark
                    letter_parent = output.add_outline_item(
                        "Correspondence", 0, parent=None)  # add bookmark
                    if len(KEY_WORDS) > 0:
                        key_words_parent = output.add_outline_item(
                            "Key words", 0, parent=None)  # add bookmark

                # date_scrape(page, input, output, Dts, date_parent)

                if len(chunks) < 5:
                    no_blank_pages += 1
                    # output.add_outline_item("Blank page", pg[0] - 1, blank_parent)
                    blank_pages.append(pg[0] - 1)

                cat_page = categorise_page(page)
                if cat_page == 0:  # no match
                    print("No match ", pg)
                    no_matches += 1
                if cat_page == 1:  # email
                    do_email_this_page(page, nextpage, input, output, Lts)
                if cat_page == 2:  # letter
                    do_letter_this_page(page, input, output, Lts)
                if cat_page == 3:  # instructions
                    txt, pg = do_instructions_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 4:  # witness statement
                    txt, pg = do_witness_statement_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 5:  # file note
                    txt, pg = do_file_note_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 6:
                    txt, pg = do_index_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 7:
                    txt, pg = do_claim_form_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 8:
                    txt, pg = do_poc_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 9:
                    txt, pg = do_DQ_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 10:
                    txt, pg = do_NTD_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 11:
                    txt, pg = do_D_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 12:
                    txt, pg = do_NAC_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 13:
                    txt, pg = do_LIST_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 14:
                    txt, pg = do_CNF_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 15:
                    txt, pg = do_offer_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 16:
                    txt, pg = do_order_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 17:
                    txt, pg = do_CRU_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 18:
                    txt, pg = do_schedule_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 19:
                    txt, pg = do_conference_note_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 20:
                    txt, pg = do_notice_of_funding_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                print("")
                print("")

        #	copy bookmarks from orginal file
        copyTOC(ftree, output)
        Dts.sort(key=sort_dates)
        Lts.sort(key=sort_dates)
        add_dates_from_correspondence_to_key_words(key_words_list, Lts, Dts)
        key_words_list.sort(key=sort_key_words)
        # paste_dates(output, Dts, date_parent)
        existingTOC = doc.get_toc(simple=False)
        if len(Lts) > 0:
            initialPage = Lts[0][2] + 1
            entry = [1, "Correspondence", initialPage]
            existingTOC.append(entry)
        paste_letters(output, Lts, existingTOC, doc, letter_parent)
        if len(KEY_WORDS) > 0:
            paste_key_words(output, key_words_list, key_words_parent)
        print("Matches: %d out of %d pages" % (len(pages) - no_matches, len(pages)))
        print("Blank pages: ", blank_pages)

        if len(other_toc) > 0:
            existingTOC.append([1, "Other", other_toc[0][2]])
        for o in other_toc:
            existingTOC.append([o[0], o[1], o[2]])

        print(existingTOC)
        doc.set_toc(existingTOC)
        doc.saveIncr()

        #        OUT_FILE = fn.name.replace(".pdf", "_.pdf")
        #        OUT_FILE = fn.name.replace(".pdf", ".pdf")
        fn.close()
        #        outputStream = open(OUT_FILE, 'wb')  # creating result pdf JCT
        #        output.write(outputStream)  # writing to result pdf JCT
        #        outputStream.close()  # closing result JCT
        if display: display.updatestatusBar(
            "Finished bookmarking." + " Matches: %d out of %d pages." % (len(pages) - no_matches, len(pages)))

def getBkMks(TOC,doc,file):
    #returns array of dict of bookmarks: {'date': xx.xx.xx, 'description': txt, 'page': page, 'label': label}
    arrBkMks=[]
    for t in TOC:
        title = gettextfromText(t[1])
        dt=getdatefromText(t[1])
        pg = t[2]-1
        label=doc[pg].get_label()
        details=t[3]
        if not 'italic' in details: details['italic']=False
        if not 'color' in details:
            details['color']=(0,0,0)
        else:
            color=tuple([round(x,4) for x in list(details['color'])]) #convert color elements to short floats
        if dt and not details['italic']:
            dic={'date': dt, 'description':title, 'page':pg, 'label': label,'file':file,'color':color}
            arrBkMks.append(dic)
    return arrBkMks

def removeDuplicateBkMks(arrBkMks):
    new_arrBkMks=[]
    old_BkMk=None
    for i in arrBkMks:
        if not old_BkMk: #always add the first one
            new_arrBkMks.append(i)
            old_BkMk=i
            continue
        if (i['date'].date() - old_BkMk['date'].date())==datetime.timedelta(0) and i['description'] == old_BkMk['description']:
            continue
        else:
            new_arrBkMks.append(i)
            old_BkMk = i
    return new_arrBkMks


def getAllBkMks(*args):
    #returns all bookmark dates from these files, sorted in ascending date order
    arrBkMks=[]
    for a in args:
        doc=fitz.open(a)
        TOC = doc.get_toc(simple=False)
        arrBkMks+=getBkMks(TOC,doc,a)
        doc.close()
    def sort_BkMks(BkMk):
        return BkMk['date'].replace(tzinfo=None)
    arrBkMks.sort(key=sort_BkMks)
    arrBkMks=removeDuplicateBkMks(arrBkMks)
    return arrBkMks

def doChronoQT(*args,**kwargs):
    arrBkMks=getAllBkMks(*args)
    folder=Path(args[0]).resolve().parent
    print(folder)
    write_chrono(arrBkMks=arrBkMks,folder=folder)


def doQT(*args, **kwargs):
    f_name=kwargs['f']
    doc=kwargs['fl']
    progress_callback=kwargs['progress_callback']
    info_callback=kwargs['info_callback']
    file_stem=Path(f_name).stem
    pbar=kwargs['progress_bar']
    other_toc = []

    if os.path.isfile(f_name) == False:
        print("O: file not found.")
        print(f_name)
        return
    with open(f_name, 'rb') as fn:
        ftree = get_toc(f_name)  # tree
        # get_labels_each_page(fn, f_name)
        pages = get_text_each_pageQT(*args,**kwargs)
        if pages is None: return
        info_callback.emit('Bookmarks...' + file_stem,pbar)
        from PyPDF2 import PdfWriter, PdfReader

        output = PdfWriter()  # open output
        input = PdfReader(fn)  # open input
        output.page_mode = "/UseOutlines"

        running = True
        licycle = cycle(pages)
        page = nextpage = next(licycle)
        count = 0
        no_matches = 0
        no_blank_pages = 0
        blank_pages = []

        Dts = []
        Lts = []
        total = len(pages)
        while count < len(pages):
            count += 1
            page, nextpage = nextpage, next(licycle)
            pg, size_page, chunks, BOW = page

            p = input.pages[pg[0] - 1]


            #print("No chunks: %d" % len(chunks))
            percentComplete = (float(count) / float(total)) * 100
            if int(percentComplete) % 2 == 0 and progress_callback:
                progress_callback.emit(int(percentComplete),pbar)

            if True:
                output.add_page(p)  # insert page
                # if p.getContents():
                #	print p.getContents()['/Filter']
                # else:
                #	print "No contents"

                # add bookmark for dates
                if count == 1:
                    # blank_parent = output.add_outline_item("Blanks", 0, parent=None)  # add bookmark
                    # date_parent = output.add_outline_item("Dates", 0, parent=None)  # add bookmark
                    letter_parent = output.add_outline_item(
                        "Correspondence", 0, parent=None)  # add bookmark
                    if len(KEY_WORDS) > 0:
                        key_words_parent = output.add_outline_item(
                            "Key words", 0, parent=None)  # add bookmark

                # date_scrape(page, input, output, Dts, date_parent)

                if len(chunks) < 5:
                    no_blank_pages += 1
                    # output.add_outline_item("Blank page", pg[0] - 1, blank_parent)
                    blank_pages.append(pg[0] - 1)

                cat_page = categorise_page(page)
                if cat_page == 0:  # no match
                    print("No match ", pg)
                    no_matches += 1
                if cat_page == 1:  # email
                    do_email_this_page(page, nextpage, input, output, Lts)
                if cat_page == 2:  # letter
                    do_letter_this_page(page, input, output, Lts)
                if cat_page == 3:  # instructions
                    txt, pg = do_instructions_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 4:  # witness statement
                    txt, pg = do_witness_statement_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 5:  # file note
                    txt, pg = do_file_note_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 6:
                    txt, pg = do_index_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 7:
                    txt, pg = do_claim_form_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 8:
                    txt, pg = do_poc_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 9:
                    txt, pg = do_DQ_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 10:
                    txt, pg = do_NTD_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 11:
                    txt, pg = do_D_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 12:
                    txt, pg = do_NAC_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 13:
                    txt, pg = do_LIST_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 14:
                    txt, pg = do_CNF_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 15:
                    txt, pg = do_offer_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 16:
                    txt, pg = do_order_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 17:
                    txt, pg = do_CRU_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 18:
                    txt, pg = do_schedule_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 19:
                    txt, pg = do_conference_note_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                if cat_page == 20:
                    txt, pg = do_notice_of_funding_this_page(page, input, output, Lts)
                    other_toc.append([2, txt, pg + 1])
                print("")
                print("")

        #	copy bookmarks from orginal file
        copyTOC(ftree, output)
        Dts.sort(key=sort_dates)
        Lts.sort(key=sort_dates)
        add_dates_from_correspondence_to_key_words(key_words_list, Lts, Dts)
        key_words_list.sort(key=sort_key_words)
        # paste_dates(output, Dts, date_parent)
        existingTOC = doc.get_toc(simple=False)
        if len(Lts) > 0:
            initialPage = Lts[0][2] + 1
            entry = [1, "Correspondence", initialPage]
            existingTOC.append(entry)
        paste_letters(output, Lts, existingTOC, doc, letter_parent)
        if len(KEY_WORDS) > 0:
            paste_key_words(output, key_words_list, key_words_parent)
        print("Matches: %d out of %d pages" % (len(pages) - no_matches, len(pages)))
        print("Blank pages: ", blank_pages)

        if len(other_toc) > 0:
            existingTOC.append([1, "Other", other_toc[0][2]])
        for o in other_toc:
            existingTOC.append([o[0], o[1], o[2]])

        doc.set_toc(existingTOC)
        doc.saveIncr()

        fn.close()

def copyTOC(ftree, output):
    # Write bookmarks for children of this node
    print(len(output.pages))

    def WriteChildren(CurrentNode, CurrentBookMark):
        if (CurrentNode.identifier != 0):  # i.e. skip root
            BkMkData = CurrentNode.data
            print(BkMkData.title, BkMkData.pageno)
            try:
                CurrentBookMark = output.add_outline_item(title=BkMkData.title, pagenum=BkMkData.pageno,
                                                          parent=CurrentBookMark)
            except Exception as e:
                print(f"Error {e}")
                pass
        for ChildNode in ftree.children(CurrentNode.identifier):
            WriteChildren(ChildNode, CurrentBookMark)

    WriteChildren(ftree.get_node(0), None)  # Write bookmarks from tree from start
    return


def sort_dates(BkMk):
    distance_from_top = get_distance_from_top_page(BkMk.chunk)
    if distance_from_top is None:
        distance_from_top = 0
    if BkMk.Dt:
        return BkMk.Dt.replace(tzinfo=None), distance_from_top
    else:
        return datetime.datetime(1066, 10, 10), distance_from_top


def sort_key_words(k):
    return k['keyword'], k['pg']


def add_dates_from_correspondence_to_key_words(key_words_list, Lts, Dts):
    for key_word in key_words_list:
        BkMks = get_bookmarks_on_page(Lts, key_word['pg'])
        # get the nearest chunk that is north of key_word chunk
        chunk = None
        vertical = 10000
        for BkMk in BkMks:
            if BkMk.chunk and key_word['chunk']:
                v = vertical_distance(BkMk.chunk, key_word['chunk'])
                if v < vertical:
                    vertical = v
                    chunk = BkMk.chunk
        if chunk:  # if we have a suitable chunk get the date and add to key_word
            key_word['Dt_txt'] = chunk.Dt_txt
            key_word['Dt'] = chunk.Dt
        else:  # get nearest non-dob date and use this instead
            BkMks = get_bookmarks_on_page(Dts, key_word['pg'])
            chunk = None
            vertical = 10000
            for BkMk in BkMks:
                if BkMk.chunk and key_word['chunk']:
                    v = vertical_distance(BkMk.chunk, key_word['chunk'])
                    if v < vertical:
                        vertical = v
                        chunk = BkMk.chunk
            if chunk:  # if we have a suitable chunk get the date and add to key_word
                key_word['Dt_txt'] = chunk.Dt_txt
                key_word['Dt'] = chunk.Dt


sys.setrecursionlimit(10000)


def print_errors():
    global error_list
    print(error_list)


def externalDrop(data, queue_to_gui=None, queue_from_gui=None, file_text=""):
    print("Data dropped:", data)
    global percentComplete

    fs = data.split("}")  # split by ;
    print(fs)
    for f in fs:
        f = f.replace('{', "").strip()
        print(f)
        if f != "":
            percentComplete = 0
            do(f, fitz.open(f), None,queue_to_gui, queue_from_gui, file_text)
