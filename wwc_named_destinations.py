import sys
from pypdf import PdfReader, PdfWriter
import fitz

def pdf_get_named_destinations(doc): #consider pdfminer.six
    ss=doc.resolve_names()
    for s in ss:
        ss[s].update({'file':doc.name})
    return ss
    #returns a list of destinations eg in one in tuple from ('name', page, order in document).
    reader = PdfReader(fh)
    destinations = reader.named_destinations                    #completely unsorted order, does not include pagenums
    L=list();
    np =  len(reader.pages)
    for PageNum in range(1,np+1) :
        ThisPage = reader.pages[PageNum-1]
        PageTop = ThisPage['/MediaBox'][3]
        for name in destinations:
            ThisDest = destinations[name]
            ThisDestPage = ThisDest.page.get_object()
            if ThisDestPage == ThisPage:
                if not ThisDest.top:
                    top=0
                else:
                    top=ThisDest.top #have to do this to identify the pagenum
                DownPage = (PageTop - top) / PageTop   # calc fraction of page down
                Position = PageNum + DownPage                   # a sortable number down the whole pdf
                L.append((name, PageNum, Position));            # put everything in a sortable list
    return L

def pdf_print_anchors ( L ) :
    for dest in L :
        name=dest[0]
        PageNum=dest[1]
        Position= round(dest[2]*100)/100
        print (f"{Position}, {name}, {PageNum}") #ThisDest.title


L=pdf_get_named_destinations(fitz.open(r"C:\Users\samsu\Dropbox\My documents\WWC Pigeon Hole\24-01-06 BURKE {213056}\Medical records\EEAS records.pdf"))
print (L)