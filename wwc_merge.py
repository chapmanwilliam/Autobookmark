from tree import treeMerge
import fitz
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

class mergeDialog(tk.Toplevel):

    def __init__(self, parent, doc, options):
        tk.Toplevel.__init__(self,parent)
        self.parent=parent
        self.doc=doc
        self.options=options
        self.count=0
        self.filepathVar=tk.StringVar()

        self.listFilePaths={} #for storing paths.

        self.displayDialog()

    def show(self):
        self.wait_window()
        return self.filepathVar.get()


    def displayDialog(self):
        self.geometry('1200x400')
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.title('Merge files')
        self.attributes('-topmost', True)
        self.tMerge = treeMerge(self, None)
        self.tMerge.pack(side=tk.TOP, fill=tk.BOTH)

        bottomFrame = tk.Frame(self)
        bottomFrame.columnconfigure(0, weight=1)
        bottomFrame.columnconfigure(1, weight=1)
        bottomFrame.pack(side=tk.TOP, fill=tk.X)

        lButton = tk.Button(bottomFrame, text='+', command=lambda: self.addFiles())
        lButton.grid(row=0, column=0, rowspan=1, sticky="NESW", padx=2, pady=2)
        rButton = tk.Button(bottomFrame, text='-', command=lambda: self.deleteFiles())
        rButton.grid(row=0, column=1, rowspan=1, sticky="NESW", padx=2, pady=2)

        lButton = tk.Button(bottomFrame, text='CANCEL', command=lambda: self.onClosing())
        lButton.grid(row=1, column=0, rowspan=1, sticky="NESW", padx=2, pady=2)
        lButton = tk.Button(bottomFrame, text='MERGE', command=lambda: self.mergeFiles())
        lButton.grid(row=1, column=1, rowspan=1, sticky="NESW", padx=2, pady=2)

        #        self.bind('<Return>', lambda i: onReturn(i))
        self.bind('<Key-Escape>', lambda i: self.onEscape(i))
        self.protocol('WM_DELETE_WINDOW', self.onClosing)

    def __del__(self):
        pass


    def addFiles(self):
        filepaths = filedialog.askopenfilenames(initialdir=self.options['lastfilePath'], title="Select file",
                                              filetypes=(("pdf files", "*.pdf"), ("all files", "*.*")))

        print(filepaths)
        self.loadFilepaths(filepaths)

    def loadFilepaths(self,filepaths):
        #adds the files to the tree
        for filepath in filepaths:
            doc=fitz.open(filepath)
            pageRange='All pages'
            size=str(int(float(os.path.getsize(filepath))/1000)) + " kb"
            noPages=doc.page_count
            bookmark=self.processbookmarkname(filepath)
            id=self.tMerge.insert('', 'end', text=os.path.basename(filepath), values=(pageRange, size, noPages, bookmark))
            self.listFilePaths[id]={'filepath':filepath, 'bookmark': bookmark, 'pageRange': pageRange}
            doc.close()

    def processbookmarkname(self,filepath):
        bookmark=os.path.splitext(filepath)[0]
        bookmark = os.path.basename(bookmark)
        bookmark=re.sub(r'(\d{2,4})-(\d{2})-(\d{2}) (.*$)',r'\4, \3/\2/\1', bookmark)
        return bookmark

    def updatelistFilePaths(self):
        for k in self.listFilePaths:
            bookmark=self.tMerge.item(k)['values'][3]
            pageRange=self.tMerge.item(k)['values'][0]
            self.listFilePaths[k]['bookmark']=bookmark
            self.listFilePaths[k]['pageRnage']=pageRange
        return self.listFilePaths

    def deleteFiles(self):
        sel=self.tMerge.deleteFull()
        for s in sel: del self.listFilePaths[s]


    def mergeFiles(self):
        filepath=make_pdf(self.updatelistFilePaths())
        if not filepath=="":
            self.filepathVar.set(filepath)
            self.onClosing()

    def onEscape(self,i):
        self.destroy()

    def onClosing(self):
        print('closing')
        self.destroy()






def make_pdf(filePaths):
    #filenames is a list of filenames to be merged
    # no file selected: treat like "QUIT"
    if not len(filePaths):  # no files there - quit
        return None
    # create time zone value in PDF format
    cdate = fitz.getPDFnow()
#    ausgabe = dlg.btn_aus.GetPath()
    pdf_out = fitz.open()  # empty new PDF document
    aus_nr = 0  # current page number in output
#    pdf_dict = {"creator": "PDF Joiner",
#                "producer": "PyMuPDF",
#                "creationDate": cdate,
#                "modDate": cdate,
#                "title": dlg.austit.Value,
#                "author": dlg.ausaut.Value,
#                "subject": dlg.aussub.Value,
#                "keywords": dlg.keywords.Value}
#    pdf_out.setMetadata(pdf_dict)  # put in meta data
    total_toc = []  # initialize TOC
    # ==============================================================================
    # process one input file
    # ==============================================================================
    warnings=[]
    for k in filePaths:
        if not os.path.exists(filePaths[k]['filepath']):
            warnings.append('File does not exist: ' + filePaths[k]['filepath'])
            continue
        doc = fitz.open(filePaths[k]['filepath'])
        max_seiten = len(doc)
        # ==============================================================================
        # user input minus 1, PDF pages count from zero
        # also correct any inconsistent input
        # ==============================================================================
        von = 0  # first PDF page number
        bis = doc.page_count-1  # last PDF page number

        von = min(max(0, von), max_seiten - 1)  # "from" must be in range
        bis = min(max(0, bis), max_seiten - 1)  # "to" must be in range
        rot = -1  # get rotation angle
        # now copy the page range
        pdf_out.insertPDF(doc, from_page=von, to_page=bis,
                          rotate=rot)
        if False:  # no ToC wanted - get next file
            continue

        incr = 1  # standard increment for page range
        if bis < von:
            incr = -1  # increment for reversed sequence
        # list of page numbers in range
        pno_range = list(range(von, bis + incr, incr))
        # standard bokkmark title = "infile [pp from-to of max.pages]"
        bm_main_title = filePaths[k]['bookmark']
        # insert standard bookmark ahead of any page range
        total_toc.append([1, bm_main_title, aus_nr + 1])
        toc = doc.get_toc(simple=False)  # get file's TOC
        last_lvl = 1  # immunize against hierarchy gaps
        for t in toc:
            lnk_type = t[3]["kind"]  # if "goto", page must be in range
            if (t[2] - 1) not in pno_range and lnk_type == fitz.LINK_GOTO:
                continue
            if lnk_type == fitz.LINK_GOTO:
                pno = pno_range.index(t[2] - 1) + aus_nr + 1
            # repair hierarchy gaps by filler bookmarks
            while (t[0] > last_lvl + 1):
                total_toc.append([last_lvl + 1, "<>", pno, t[3]])
                last_lvl += 1
            last_lvl = t[0]
            t[2] = pno
            total_toc.append(t)

        aus_nr += len(pno_range)  # increase output counter
        doc.close()
        doc = None

    # ==============================================================================
    # all input files processed
    # ==============================================================================
    if total_toc:
        pdf_out.set_toc(total_toc)
    defaultpath = os.path.expanduser('~')
    filepath=saveAs(pdf_out, defaultpath)
    pdf_out.close()
    print (warnings)
    if len(warnings)>0:
        txt="\n".join(warnings)
        messagebox.showwarning('Warnings',txt)
    return filepath


def saveAs(doc, defaultpath='/'):
    filepath = filedialog.asksaveasfilename(initialdir=defaultpath, title="Select file",
                                                 filetypes=(("pdf files", "*.pdf"), ("all files", "*.*")))
    if filepath:
        doc.save(filepath)
    return filepath

