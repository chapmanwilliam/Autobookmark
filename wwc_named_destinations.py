import sys
from pypdf import PdfReader, PdfWriter
import fitz

def pdf_get_named_destinations(doc):
    #returns list of named destinations
    ss=doc.resolve_names()
    for s in ss:
        ss[s].update({'file':doc.name})
    return ss

def insert_named_destination(doc,page,name):
    #inserts a named destination to this page
    fitz.open(
        r"C:\Users\samsu\Dropbox\My documents\WWC Pigeon Hole\24-01-06 BURKE {213056}\Medical records\EEAS records.pdf")

    #update_object(xref, obj_str, page=None)  - to create a new object
    #xref_set_key() - change key value
    #get_new_xref() - #To create an (empty) object with this number use doc.update_xref(xref, "<<>>")
    pass


#L=pdf_get_named_destinations(fitz.open(r"C:\Users\samsu\Dropbox\My documents\WWC Pigeon Hole\24-01-06 BURKE {213056}\Medical records\EEAS records.pdf"))
#print (L)