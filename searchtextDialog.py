import tkinter as tk
import fitz
from utilities import annot_name

suffix='search-highlight'



class searchtextDialog():
    def __init__(self, parent, display):


        self.parent=parent
        self.display=display
        self.doc=display.doc
        self.count=0
        self.searchPg=self.display.cur_page
        self.oldsearchPg=-1
        self.oldsearch=""

        self.displayDialog()

    def __del__(self):
        pass

    def searchForward(self, search, fromPg=0):
        if fromPg>=self.doc.page_count:
            self.searchPg=self.doc.page_count-1
            return
        for pg in range(fromPg,self.doc.page_count):
            self.display.updatestatusBar("Searching page " + str(pg+1) + " out of " + str(self.doc.page_count))
            if self.highlight(search,pg):
                self.searchPg=pg
                self.oldsearchPg=self.searchPg
                return True
        return False

    def searchBackward(self, search, fromPg=0):
        if fromPg<0:
            self.searchPg=0
            return
        for pg in range(fromPg,-1,-1):
            self.display.updatestatusBar("Searching page " + str(pg+1) + " out of " + str(self.doc.page_count))
            if self.highlight(search,pg):
                self.searchPg=pg
                self.oldsearchPg=self.searchPg
                return True
        return False


    def clearAll(self):
        for pg in range(0,self.doc.page_count):
            percent=int(float(pg)*100/float(self.doc.page_count))
            if percent % 2==0:
                self.display.updateprogressBar(percent)
                self.display.updatestatusBar("Clearing highlights from page " + str(pg+1) + " out of " + str(self.doc.page_count))
            self.clearHighlight(pg)
        self.display.updatestatusBar("Finished clearing highlights.")
        self.display.updateprogressBar(0)
        self.display.refreshallPages()

    def clearHighlight(self,pg):
        if pg<0 or pg>=self.doc.page_count: return
        page=self.doc[pg]
        for annot in page.annots():
            info = annot.info
            id = info['id']
            if id.find(annot_name + suffix) > -1:
                page.deleteAnnot(annot)
        self.display.dlist_tab[pg]=None

    def highlight(self,search,pg, clear_old=True):
        fitz.TOOLS.set_annot_stem(annot_name + suffix)
        page = self.doc[pg]
        quads = page.searchFor(search, quads=True)
        if quads:
            self.count += 1
            if clear_old: self.clearHighlight(self.oldsearchPg)
            page.addHighlightAnnot(quads)
            self.display.addpageHistory(pg)
            self.display.refreshPage(pg)
            self.display.setPage(pg)
            self.display.setPgDisplay()
            return True


    def searchAll(self, search):
        count=0
        cur_page=self.display.cur_page
        for pg in range(0,self.doc.page_count):
            percent=int(float(pg)*100/float(self.doc.page_count))
            if percent % 2==0:
                self.display.updateprogressBar(percent)
                self.display.updatestatusBar("Searching page " + str(pg+1) + " out of " + str(self.doc.page_count))
            if self.highlight(search,pg, clear_old=False): count+=1
        self.display.updatestatusBar("Finished searching.")
        self.display.updateprogressBar(0)
        self.display.refreshallPages()
        self.display.addpageHistory(cur_page)
        self.display.setPage(cur_page)

    def displayDialog(self):

        def clearAll():
            self.clearAll()

        def search(search):
            if search=="": return
            self.searchForward(search,self.searchPg)

        def searchAll(search):
            if search=="" : return
            self.searchAll(search)

        def onReturn(i):
            search=e1.get()
            if search=="" : return
            if search==self.oldsearch: self.searchPg+=1
            if not self.searchForward(search,self.searchPg): self.searchPg-=1
            self.oldsearch=search

        def onForward():
            search=e1.get()
            if search=="" : return
            if search==self.oldsearch: self.searchPg+=1
            if not self.searchForward(search,self.searchPg): self.searchPg-=1
            self.oldsearch=search

        def onBackward():
            search=e1.get()
            if search=="" : return
            if search==self.oldsearch: self.searchPg-=1
            if not self.searchBackward(search,self.searchPg): self.searchPg+=1
            self.oldsearch=search

        def onClosing():
            print('closing')
            self.display.updatestatusBar("")
            searchWindow.destroy()

        def onEscape(i):
            searchWindow.destroy()

        searchWindow = tk.Toplevel(self.parent)
        searchWindow.title('Search text')
        searchWindow.attributes('-topmost', True)
        searchWindow.resizable(True,False)

        searchFrame=tk.LabelFrame(searchWindow, text='Search')
        searchFrame.pack(fill=tk.X,padx=5,pady=5)

        tk.Label(searchFrame, text="Text:").pack(side=tk.LEFT, padx=5,pady=5)
        e1 = tk.Entry(searchFrame)
        e1.pack(side=tk.LEFT,fill=tk.X,expand=1,padx=5,pady=5)

        frameButtons=tk.Frame(searchWindow)
        frameButtons.pack(fill=tk.X, padx=5,pady=5)
        tk.Button(frameButtons, text='Search', command=lambda: search(e1.get())).pack(side=tk.LEFT,fill=tk.X,expand=1)
        tk.Button(frameButtons, text='Search All', command=lambda: searchAll(e1.get())).pack(side=tk.LEFT,fill=tk.X,expand=1)
        tk.Button(frameButtons, text='Clear All', command=lambda: clearAll()).pack(side=tk.LEFT,fill=tk.X,expand=1)

        bottomFrame = tk.Frame(searchWindow)
        bottomFrame.pack(fill=tk.X,padx=5,pady=5)

        tk.Button(bottomFrame, text='<', command=lambda: onBackward()).pack(side=tk.LEFT, fill=tk.X, expand=1)
        tk.Button(bottomFrame, text='>', command=lambda: onForward()).pack(side=tk.LEFT, fill=tk.X, expand=1)

        e1.focus_set()

        searchWindow.bind('<Return>', lambda i: onReturn(i))
        searchWindow.bind('<Key-Escape>', lambda i: onEscape(i))
        searchWindow.protocol('WM_DELETE_WINDOW', onClosing)

