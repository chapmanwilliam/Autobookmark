import re
import sys
from collections import OrderedDict
from wwc_named_destinations import pdf_get_named_destinations
import fitz
from pikepdf import Pdf, Page, NameTree, make_page_destination, Dictionary,Name,Array

#WILLIAM CHAPMAN 29/12/2020
#READS AND WRITES PAGE LABELS TO PDF
#READING:
# --- getpgLabelMapping(doc) returns tuple:
#    dict - an ordered dictionary of page labels. For each page label there is a tuple of associated page numbers
#    arr_labels - a list page labels (integers) from 0 to doc.page_count-1. arr_labels[pgNo] returns the page label associated with pgNo
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
    root_xref = doc.pdf_catalog()
    return doc.xref_object(root_xref, compressed=True)  # return object definition

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

def getrelevantPartCatalogDests(cat, doc):
    #returns the part of the string relevant to catalog
    st=cat.find("/Dests")
    if st<0:
        print("'%s' has no destinations" % doc.name)
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
        exp = doc.xref_object(ref, compressed=True)
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

    arr_labels = [None] * doc.page_count   # for each page, what is the page label
    dict = {}   # for each pagelabel, there is a tuple of associated pages
    if len(labels) > 0:
        for i in range(0, len(labels)):
            l1 = labels[i]
            if len(labels) > i + 1:
                l2 = labels[i + 1]
                end_page = l2['startpage']
            else:
                end_page = doc.page_count
            i = 0
            for c in range(l1['startpage'], end_page):
                lab = construct_label(l1['style'], l1['prefix'], l1['firstpagenum'] + i)
                arr_labels[c] = lab
                if lab in dict:
                    dict[lab]['page']=dict[lab]['page']+(c,) #if there's repeat page_label add page to tuple
                else:
                    dict[lab]={'page':(c,),'file':doc.name} #the first page label of this name add page as tuple
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


def create_list_names(doc, names):
    #where names is dictionary like {'name1': {'page' : page_no1, 'dest': '/FitH 842', 'file': 'C://'}
    #returns a limits string and a names string for inserting into pdf
    #TODO: need to sort names alphabetically in ascending order
    names_pdf_string=''
    first_name=None
    last_name=None
    for name in names:
        if first_name is None: first_name=name
        name_string='(' + name + ')'
        pg_no=names[name]['page'][0]
        dest='/Fit'
        page_string='['+str(doc[pg_no].xref) + " 0 R"+dest +']'

        new_xref,xref_str=create_new_xref(doc) #new object with destination
        doc.xref_set_key(new_xref,'D', page_string)
        names_pdf_string += name_string + xref_str
    names_pdf_string='[' + names_pdf_string + ']'
    last_name=name
    limits_pdf_string="[(" + first_name + ")("+last_name+")]"
    return limits_pdf_string, names_pdf_string

def create_new_xref(doc):
    new_xref=doc.get_new_xref()
    xref_str=' ' + str(new_xref)+' 0 R'
    doc.update_object(new_xref, "<<>>")
    return new_xref,xref_str

def create_new_kid(doc,xref_kids):
    new_xref, xref_str=create_new_xref(doc)
    tup = doc.xref_get_key(xref_kids, 'Kids')
    arr_str=tup[1].strip('[]')
    arr_str+=xref_str
    arr_str='[' + arr_str + ']'
    doc.xref_set_key(xref_kids,'Kids',arr_str)
    print(new_xref)
    return new_xref

if __name__ == "__main__":
    def get_xref_names():
        return int(doc.xref_get_key(doc.pdf_catalog(), 'Names')[1][:-4])
    def get_xref_dests():
        cat_xref=get_xref_names()
        for key in doc.xref_get_keys(cat_xref):
            tup = doc.xref_get_key(cat_xref, key)
            if key=='Dests':
                return int(tup[1][:-4])

    flag=False
    def get_keys(x_ref,flag):
        for key in doc.xref_get_keys(x_ref):
            if key=='Names': flag=True
            tup=doc.xref_get_key(x_ref, key)
            print(x_ref, key, "=", tup)
            if flag:
                if tup[0]=='xref':
                    new_xref=int(tup[1][:-4])
                    get_keys(new_xref,flag)

    def get_existing_nds(pdf):
        #returns array of tuples ('name', xref)
        try:
            nt = NameTree(pdf.Root.Names.Dests)
            try:
                d=pdf.Root.Names.Dests.Names
            except:
                pdf.Root.Names.Dests.Names = Array()
                pdf.Root.Names.Dests.Names.append(Dictionary())
                pdf.Root.Names.Dests.Names = Array()
            #return '['+''.join([(f'({k}){nt[k].objgen[0]} 0 R') for k in nt.keys()])+']'
        except:
            nt = NameTree.new(pdf)
            pdf.Root.Names.Dests = nt.obj
            pdf.Root.Names.Dests.Names = Array()
            pdf.Root.Names.Dests.Names.append(Dictionary())
            pdf.Root.Names.Dests.Names = Array()

        return nt

    def join_nds(a,b):
        if a:
            a=a.strip('[]')
        else:
            a=''
        if b:
            b=b.strip('[]')
        else:
            b=''
        return '[' + a+b + ']'

    #print(get_existing_nds('x'))
    #    doc=fitz.open(r"C:\Users\samsu\Dropbox\My documents\WWC Pigeon Hole\22-04-20 HD v Wiltshire Police\Appeal\23-11-02 Permission granted HD v Wiltshire\Judgement first instance\CJ v Chief Constable of Wiltshire [2022] EWHC 1661 (QB).pdf")
    doc=fitz.open(r"C:\Users\samsu\Dropbox\My documents\WWC Pigeon Hole\22-04-20 HD v Wiltshire Police\Appeal\23-11-02 Permission granted HD v Wiltshire\Judgement first instance\Document1 test.pdf")

    d, arr = getpgLabelMapping(doc)
#    nd=pdf_get_named_destinations(doc)
#    print('nd',nd)
    limits,names=create_list_names(doc,d)

    pdf = Pdf.open(
        r"C:\Users\samsu\Dropbox\My documents\WWC Pigeon Hole\22-04-20 HD v Wiltshire Police\Appeal\23-11-02 Permission granted HD v Wiltshire\Judgement first instance\Document1 test.pdf",
    allow_overwriting_input=True)
    nt=get_existing_nds(pdf)
    print(nt.obj)


    dest = make_page_destination(pdf, page_num=0, page_location="Fit")
    pdf.Root.Names.Dests.Names.extend(["XX1", dest])  #combined=join_nds(get_existing_nds(doc),names)
    #print(combined)
    cat_xref=doc.pdf_catalog()


    #print(create_list_names(doc,{'Test1': 0, 'Test2':1}))
    #print(create_list_names(doc,d))

    #limits,names=create_list_names(doc,d)
    #new_kid_xref=create_new_kid(doc,2776)
    #print(get_xref_names())
#    print(get_xref_dests())

    #get_keys(cat_xref ,False)

#    print ('proposal', combined)
    #print('before',doc.xref_get_key(get_xref_dests(),'Names'))
#    doc.xref_set_key(get_xref_dests(),'Names',combined)

    #print('after', doc.xref_get_key(get_xref_dests(), 'Names'))

    #get_keys(cat_xref,False)

    doc.close()

 #   pdf = Pdf.open(filename_or_stream=r"C:\Users\samsu\Dropbox\My documents\WWC Pigeon Hole\22-04-20 HD v Wiltshire Police\Appeal\23-11-02 Permission granted HD v Wiltshire\Judgement first instance\Document1 test.pdf",
  #                 allow_overwriting_input=True)
    print(nt.obj)
    pdf.save(pdf.filename)
    #1 - if no Names/Dests ==> create Names/Dests/Kids (an array)
    #2 - if Names/Dests/Names ==> i) copy Names ii) create Names/Dests/Kids
    #3 -




    #doc.xref_set_key(new_kid_xref,'Limits',limits)
    #doc.xref_set_key(new_kid_xref,'Names',names)

    #doc.saveIncr()




    #print(get_xref_names())
    #print(get_xref_dests())
    #Type, Parent, Contents, MediaBox, Resources, Group


    #<</Root/Names<<Dests<<Kids ['list of xrefs']
    #<<Limits['start and finish of list of names as strings']
    #<<Names[%s xref, %s xref]
    #xref: /D[xref, /XYZ]

    #48 J1 - this has some highlights on it page 3
    #48 /D xref is /Annots, /Contents /Group /MediaBox /Parent /Resources /Type ('name', '/Page')

    #48 O R is the page!
    #48 Annots = ('xref', '1250 0 R')
    #48 Contents = ('xref', '49 0 R')
    #48 Group = ('dict', '<</CS/DeviceRGB/S/Transparency/Type/Group>>')
    #48 MediaBox = ('array', '[0 0 595.45 841.7]')
    #48 Parent = ('xref', '3 0 R') #this is list of pages
    #48 Resources = ('dict', '<</Font<</FAAAAI 8 0 R/FAAAFB 51 0 R>>>>')
    #48 Type = ('name', '/Page')

    #57 O R is the page!
    #57 - J10 -this has no highlights - page 5
    #57 Type = ('name', '/Page') #the same
    #57 Parent = ('xref', '3 0 R') # this is list of pages
    #57 Contents = ('xref', '58 0 R') #different
    #57 MediaBox = ('array', '[0 0 595.45 841.7]') #the same
    #57 Resources = ('dict', '<</Font<</FAAAAI 8 0 R/FAAAFB 51 0 R>>>>') #the same
    #57 Group = ('dict', '<</Type/Group/S/Transparency/CS/DeviceRGB>>') #the same

    #So where does it note which is the correct page for the destination? Or is it a copy of the page?
    #Yes, it's a straight copy of the page. It's simply a pointer to the page