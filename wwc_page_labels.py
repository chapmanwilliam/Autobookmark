import re
import sys
from collections import OrderedDict

#WILLIAM CHAPMAN 29/12/2020
#READS AND WRITES PAGE LABELS TO PDF
#READING:
# --- getpgLabelMapping(doc) returns tuple:
#    dict - an ordered dictionary of page labels. For each page label there is a tuple of associated page numbers
#    arr_labels - a list page labels (integers) from 0 to doc.pageCount-1. arr_labels[pgNo] returns the page label associated with pgNo
#WRITING
# --- update_catalog_nums(doc, labels)
# labels is a list. Each element is  {'startpage': '0', 'prefix': '', 'style': 'D', 'firstpagenum': '1'}
# labels must be listed in order of 'startpage'

#Use these to mark boundaries in the catalog file
catalogEntries=['Type', 'Version', 'Pages', 'PageLabels', 'Names', 'Dests', 'ViewerPreferences', 'PageLayout', \
                'PageMode', 'Outlines', 'Threads', 'OpenAction', 'AA', 'URI', 'AcroForm', \
                'Metadata', 'StructTreeRoot', 'MarkInfo', 'Lang', 'SpiderInfo', 'OutputIntents', \
                'PlaceInfo', 'OCProperties', 'Perms', 'Legal', 'Requirements', 'Collection', 'NeedsRendering']


def getLabel(page):
    #returns the page label for this page
    pgNo=page.number
    labels=get_labels_from_doc(page.parent)
    # Label looks like: l = {'startpage': '0', 'prefix': '', 'style': 'D', 'firstpagenum': '1'}

    #do a binary search on labels
    def binary_search_recursive(labels, element, start, end):
        if start > end:
            return -1

        mid = (start + end) // 2
        if element== labels[mid]['startpage'] or start==end:
            if element<labels[mid]['startpage']: return max(0,mid-1)
            if element>labels[mid]['startpage']: return min(len(labels)-1,mid+1)
            return mid

        if element < labels[mid]['startpage']:
            return binary_search_recursive(labels, element, start, mid-1)
        else:
            return binary_search_recursive(labels, element, mid+1, end)

    index=binary_search_recursive(labels,pgNo,0,len(labels)-1)
    prefix=labels[index]['prefix']
    style=labels[index]['style']
    pagenumber=pgNo-labels[index]['startpage']+labels[index]['firstpagenum']
    result=construct_label(style,prefix,pagenumber)
    return result

#Getting the page labels from the catalog
def getpgLabelMapping(doc):
    #returns mapping
    labels=get_labels_from_doc(doc)
    dict, arr_labels = set_labels(doc, labels) #dict is dictionary of labels return tuple of pages, arr_labels is list of page labels in page order
    return dict, arr_labels

def _get_labels_from_doc(doc): #i.e .jorji's code
    ls=doc._get_page_labels()
    labels=_get_labels(ls)
    return labels

def get_labels_from_doc(doc):
    #returns a list of labels
    #each label looks like this label = {'startpage': '0', 'prefix': '', 'style': 'D', 'firstpagenum': '1'}
    cat = get_catalog(doc)
    s=getrelevantPartCatalog(cat, doc)
    ls=doc._get_page_labels()
    lbs=_get_labels(ls)
    s = expand_indirect_references(doc,s)
    labels=get_labels(s)
    return labels

def get_catalog(doc):
    #returns the catalog
    root_xref = doc.PDFCatalog()  # get xref of the /Catalog
    return doc.xrefObject(root_xref, compressed=True)  # return object definition

def getrelevantPartCatalog(cat, doc):
    #returns the part of the string relevant to catalog
    st=cat.find("/PageLabels")
    if st<0:
        print("'%s' has no page labels" % doc.name)
        return None
    #Go through catalog of types: https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf, page 141
    en=9999999 #insanely high number
    for category in catalogEntries:
        res=cat.find("/" + category,st)
        if res>st:
            if res<en: en=res
    str=cat[st: en]
    return str

def expand_indirect_references(doc, str):
    #Adobe pdf stores some labels as indirect references. So these have to be expanded first.
    if not str: return None
    x = re.finditer('(\d+) (\d+) R', str, re.DOTALL)
    count=0
    for m in x:
        ref = int(m[1])
        exp = doc.xrefObject(ref, compressed=True)
        str = re.sub(m[0], exp, str)
        count+=1
    if count>0: str=expand_indirect_references(doc,str) #repeat until expanding exhausted
    return str



def _get_labels(ls): #i.e. for jorji's code
    #ls is is a list like
    #[(0, '<</P(TOC_)/S/r/St 1>>'), (112, '<</S/D/St 3>>')
    labels=[]
    if len(ls)>0:
        for l in ls:
            label = {}
            label['startpage']=l[0]
            x1=l[1].find('<<')
            x2=l[1].find('>>')
            flechedStr=l[1][x1+2:x2]
            label['prefix'], label['style'], label['firstpagenum'] = parse_flags(flechedStr)
            labels.append(label)
        # check if labels start at page 0
        if len(labels) > 0:
            s = int(labels[0]['startpage'])
            if s > 0:
                # create an initial label
                l = {'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1}
                labels.insert(0, l)
    else:
        # create an initial label
        l = {'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1}
        labels.append(l)
    return labels


def get_labels(str):
    # label looks like this: 33<</P(A)/S/r/St3>>
    labels = []
    if not str == None:
        x = re.finditer('((\d+)( )*<<(.*?)>>)', str, re.DOTALL)
        for m in x:
            label = {}
            label['startpage'] = int(m[2])
            label['prefix'], label['style'], label['firstpagenum'] = parse_flags(m[4])
            labels.append(label)
        # check if labels start at page 0
        if len(labels) > 0:
            s = int(labels[0]['startpage'])
            if s > 0:
                # create an initial label
                l = {'startpage': '0', 'prefix': '', 'style': 'D', 'firstpagenum': 1}
                labels.insert(0, l)
    else:
        # create an initial label
        l = {'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1}
        labels.append(l)
    return labels

def parse_flags(str):
    # flags looks like this /P(A)/S/r/St3
    prefix = ''
    style = ''
    firstpagenum = ''
    # look for prefix
    x = re.search('\/P( )*\((.*)\)', str)
    if x: prefix = x.group(2)
    # look for style
    x = re.search('\/S( )*\/(\w)', str)
    if x: style = x.group(2)
    # look for startnumber
    x = re.search('St( )*(\d+)', str)
    if x:
        firstpagenum = int(x.group(2))
    else:
        firstpagenum = 1

    return prefix, style, firstpagenum


def set_labels(doc, labels):

    arr_labels = [None] * doc.pageCount   # for each page, what is the page label
    dict = OrderedDict()   # for each pagelabel, there is a tuple of associated pages
    if len(labels) > 0:
        for i in range(0, len(labels)):
            l1 = labels[i]
            if len(labels) > i + 1:
                l2 = labels[i + 1]
                end_page = l2['startpage']
            else:
                end_page = doc.pageCount
            i = 0
            for c in range(l1['startpage'], end_page):
                lab = construct_label(l1['style'], l1['prefix'], l1['firstpagenum'] + i)
                arr_labels[c] = lab
                if lab in dict:
                    dict[lab].append(c)
                else:
                    dict[lab]=[(c)]
                i = i + 1
    else:
        c = 0
        for page in doc:
            arr_labels[c] = str(c + 1)
            dict[str(c + 1)] = [(c)]
            c = c + 1
    return dict, arr_labels


def construct_label(style, prefix, pagenumber):
    n_str = ""
    if style == 'D':
        n_str = str(pagenumber)
    if style == 'r':
        n_str = integerToRoman(pagenumber).lower()
    if style == 'R':
        n_str = integerToRoman(pagenumber).upper()
    if style == 'a':
        n_str = integerToLetter(pagenumber).lower()
    if style == 'A':
        n_str = integerToLetter(pagenumber).upper()
    result = prefix + n_str
    return result

def integerToLetter(i):
    ls = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
          'W', 'X', 'Y', 'Z']
    m = int((i - 1) / 26)  # how many times over
    n = (i % 26) - 1  # remainder
    str_t = ""
    for x in range(0, m + 1):
        str_t = str_t + ls[n]
    return str_t


def integerToRoman(num):
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])


#Constructing the catalog
def create_label_str(label):
    # label is dict  {startpage,prefix,style,firstpagenum}
    s = ''
    s += str(label['startpage'])
    s += '<<'
    if not label['prefix'] == '': s += '/P(' + label['prefix'] + ')'
    if not label['style'] == '': s += '/S/' + label['style']
    if not label['firstpagenum'] == '': s += '/St ' + str(label['firstpagenum'])
    s += '>>'
    return s


def create_nums(labels):
    s = "Nums["
    for label in labels:
        s += create_label_str(label)
    s += ']'
    return s

def _create_nums(labels): #jorji's code
    s=""
    for label in labels:
        s += create_label_str(label)
    return s


def create_PageLabels(labels):
    nums=create_nums(labels)
    s = '/PageLabels <</'
    s += nums
    s += '>>'
    return s


def _update_catalog_nums(doc,labels):
#    /PageLabels<</Nums[0<</S/D>>2<</S/r>>8<</S/D>>]>> % names given to pages
        print(labels)
        print(_create_nums((labels)))
        doc._set_page_labels(_create_nums(labels))

def update_catalog_nums(doc, labels):
    #    /PageLabels<</Nums[0<</S/D>>2<</S/r>>8<</S/D>>]>> % names given to pages
    cat=get_catalog(doc)
    oldStr=getrelevantPartCatalog(cat,doc)
    newStr=create_PageLabels(labels)
    if oldStr:
        new_cat=cat.replace(oldStr,newStr)
    else:
        #need to add to catalog
        new_cat=cat+newStr
#    print (new_cat)

    root_xref = doc.PDFCatalog()  # get xref of the /Catalog
    try:
        doc.updateObject(root_xref, new_cat)
    except:
        sys.exit("Problem saving the catalog.")
