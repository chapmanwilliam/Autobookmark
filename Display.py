import os
import ocrmypdf
import time
import sys
import fitz
from utilities import get_colour, get_style, annot_name,verticestoQuads
import dateparser
import webbrowser
from tocDialog import tocDialog
from hyperlinkDialog import hyperlinkDialog
from rotateDialog import rotateDialog
from paginateDialog import paginateDialog
from wwc_merge import mergeDialog
import wwc_paginatepdf as PG
import wwc_hyperlinkpagerefs as HP
import wwc_AutoBookmarker as AB
import wwc_TOC as TC
import wwc_paginatepdf as PG
from wwc_gui_config import clockwise_location, anticlockwise_location, chrono_location, documents_location, bookmark_tab_location, delete_location, target_location, print_location, asterisk_location, order_location, link_location, book_location, table_location, search_location, left_location, right_location, settings_location, open_location, save_location, close_location, bookmark_location, CreateToolTip
from RubberBand import rubberBand
from wwc_parsebookmark import getdatefromText, getdatefromNode, gettextfromText, gettextpartDate, isValidDate, getdayofWeek
import shelve
from OrderPages import orderPages
from wwc_page_labels import getpgLabelMapping, getLabel
from printing import printDialog
from searchtreeDialog import searchtreeDialogBookmarks, searchtreeDialogChrono
from searchtextDialog import searchtextDialog
from tree import treebookMarks, treeChrono

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class thumbnail(tk.Button):
    def __init__(self, parent, page, img, buttonFrame, display, **kw):
        super().__init__(parent, **kw)
        self.page=page
        self.imageStore=img
        self.display=display
        self.buttonFrame=buttonFrame
        self.bind('<Button-1>', self.onClick)
    def onClick(self, event):
        self.display.setPage(self.page)


def full_screen(evt=None):
    # checks if the window is in fullscreen
    if root.attributes('-fullscreen'):
        root.attributes('-fullscreen',1)
        # Remove the borders and titlebar
        root.overrideredirect(True)
        root.overrideredirect(False)

class display():
    next_id=0

    def __init__(self, root, filepath=None):

        self.cur_page = 0

        self.id=display.next_id
        display.next_id+=1

        self.imageid=None #for storing image id

        self.doc = None
        self.sliderVar=tk.IntVar()

        # allocate storage for page display lists
        self.dlist_tab = [None] * 1

        test_root = tk.Tk()
        max_width = test_root.winfo_screenwidth() - 20
        max_height = test_root.winfo_screenheight() - 135
        self.max_size = (max_width, max_height)
        test_root.destroy()
        del test_root

        self.displayWindow = root

        geo=str(int(0.5*self.max_size[0])) + 'x' + str(self.max_size[1])
        self.displayWindow.geometry(geo)
        self.layout()

        self.options = self.loadOptions()
        if filepath:
            if os.path.isfile(filepath):
                self.options['lastFile']=filepath
                self.openlastFile(self.options)
        else:
            self.openlastFile(self.options)

        self.pageHistory=[0] #an array for tracking page history
        self.pageHistoryIndex=0 #where we are in pageHistory
        self.docHistory=[None] #an array for doc history
        self.docHistoryIndex=0 #where we are in docHistory


        print(openFiles)


        #Bindings
        if 'win32' in sys.platform:  # windows
            root.bind('<Shift-Control-f>',self.shiftcontrolF)
            root.bind('<Shift-Control-F>',self.shiftcontrolF)
            root.bind('<Control-m>',self.ControlM)
            root.bind('<Control-M>',self.ControlM)
            root.bind('<Control-f>',self.ControlF)
            root.bind('<Control-F>',self.ControlF)
            root.bind('<Control-s>',self.ControlS)
            root.bind('<Control-S>',self.ControlS)
            root.bind('<Control-p>',self.ControlP)
            root.bind('<Control-P>',self.ControlP)
            root.bind('<Control-O>',self.ControlO)
            root.bind('<Control-o>',self.ControlO)
            root.bind('<Control-.>',self.ControlDot)
            root.bind('<Control-d>',self.ControlD)
            root.bind('<Control-D>',self.ControlD)
            root.bind('<Control-w>',self.ControlW)
            root.bind('<Control-W>',self.ControlW)
            root.bind('<Control-z>',self.ControlZ)
            root.bind('<Control-Z>',self.ControlZ)
            root.bind('<Control-y>',self.ControlY)
            root.bind('<Control-Y>',self.ControlY)
            root.bind('<Shift-Control-z>',self.ControlY)
            root.bind('<Shift-Control-Z>',self.ControlY)
            root.bind('<Control-r>',self.ControlR)
            root.bind('<Control-R>',self.ControlR)
        elif 'darwin':  # OS X
            root.bind('<Shift-Command-f>',self.shiftcontrolF)
            root.bind('<Shift-Command-F>',self.shiftcontrolF)
            root.bind('<Command-m>',self.ControlM)
            root.bind('<Command-M>',self.ControlM)
            root.bind('<Command-f>',self.ControlF)
            root.bind('<Command-F>',self.ControlF)
            root.bind('<Command-s>',self.ControlS)
            root.bind('<Command-S>',self.ControlS)
            root.bind('<Command-p>',self.ControlP)
            root.bind('<Command-P>',self.ControlP)
            root.bind('<Command-O>',self.ControlO)
            root.bind('<Command-o>',self.ControlO)
            root.bind('<Command-.>',self.ControlDot)
            root.bind('<Command-d>',self.ControlD)
            root.bind('<Command-D>',self.ControlD)
            root.bind('<Command-w>',self.ControlW)
            root.bind('<Command-W>',self.ControlW)
            root.bind('<Command-z>',self.ControlZ)
            root.bind('<Command-Z>',self.ControlZ)
            root.bind('<Command-y>',self.ControlY)
            root.bind('<Command-Y>',self.ControlY)
            root.bind('<Shift-Command-z>',self.ControlY)
            root.bind('<Shift-Command-Z>',self.ControlY)
            root.bind('<Command-r>',self.ControlR)
            root.bind('<Command-R>',self.ControlR)
        else:
            raise RuntimeError("Unsupported operating system")

    def ControlR(self,event):
        self.rotateDialog()

    def shiftleftArrow(self,event):
        self.dechistPg()

    def shiftrightArrow(self,event):
        self.inchistPg()

    def leftArrow(self,event):
        self.decPg()

    def rightArrow(self,event):
        self.incPg()

    def ControlZ(self, event):#Undo
        self.undo()

    def ControlY(self, event):#Redo
        self.redo()

    def ControlD(self,event):
        self.setDestination()

    def ControlW(self,event):
        self.closeFile()

    def ControlDot(self,event):
        self.loadoptionsWindow()

    def ControlM(self,event):
        self.merge()

    def ControlO(self,event):
        self.openFile()

    def ControlP(self,event):
        print('printing')
        self.printPDF()

    def ControlS(self,event):
        self.save()

    def ControlF(self,event):
        self.searchDialog()

    def shiftcontrolF(self,event):
        self.searchText()

    def configButtons(self):
        #sets buttons and toolbars
        if self.doc:
            if PG.isPaginated(self.doc):
                self.toolsMenu.entryconfigure(0,label='Remove pagination') #Paginate
            else:
                self.toolsMenu.entryconfigure(0,label='Paginate') #Paginate
            if TC.isTOC(self.doc, self):
                self.toolsMenu.entryconfigure(1,label='Remove TOC') #TOC
            else:
                self.toolsMenu.entryconfigure(1,label='Add TOC') #TOC


    def reset(self):
        openFiles[self.id] = {'filepath': self.filepath, 'class': self}
        try:
            if self.doc:
                self.doc.add_default_label()
                self.dlist_tab = [None] * self.doc.page_count
                self.configButtons()
                self.vbar.config(to=self.doc.page_count)
                self.fillTree()
                self.displayWindow.title(os.path.basename(self.filepath))
                self.setPage()
            else:
                self.cur_page = 0
                self.vbar.config(to=1)
        except:
            print('Error opening')


    #file functions
    def openFile(self):
        options = self.loadOptions()
        if not os.path.exists(options['lastfilePath']): options['lastfilePath'] = '/'
        filepath = filedialog.askopenfilename(initialdir=options['lastfilePath'], title="Select file",
                                              filetypes=(("pdf files", "*.pdf"), ("all files", "*.*")))

        self.displayWindow.focus_force()
        if filepath == "":
            return
        elif self.doesFileExist(filepath):
            self.filepath=filepath
            options['lastFile'] = self.filepath
            options['lastfilePath'] = os.path.dirname(self.filepath)
            self.saveOptions(options)
            if self.doc: #we already have a doc open so reopen
                newCl=display(tk.Toplevel(), self.filepath)
                openFiles[newCl.id]={'filepath':filepath, 'class': newCl}
            else:
                self.doc = fitz.open(self.filepath)
            self.reset()
            self.scaleChange(1)

    def closeFile(self):
        self.doc.close()
        self.doc=None
        self.filepath=""
        self.emptyTree()
        self.canvas.delete('all')
        self.reset()
        self.setPgDisplay()
        self.displayWindow.title(os.path.basename('PDFUtility'))

    def merge(self):
        options = self.loadOptions()
        filepath=mergeDialog(self.displayWindow,self.doc,options).show()
        print(filepath)
        if not filepath=="":
            newCl=display(tk.Toplevel(),filepath)
            openFiles[newCl.id]={'filepath': filepath, 'class': newCl}
        print(openFiles)


    def openlastFile(self, options):
        if os.path.isfile(options['lastFile']):
            self.filepath = options['lastFile']
            self.doc = fitz.open(self.filepath)
            self.reset()
        else:
            options['lastFile'] = ''
            self.saveOptions(options)

    def doesFileExist(self,f):
        result = os.path.isfile(f)
        if f == "":
            messagebox.showerror(title="Error", message="No file selected.")
        elif not result:
            messagebox.showerror(title="Error", message="File does not exist")
        return result


    def saveAs(self):
        options = self.loadOptions()
        if not os.path.exists(options['lastfilePath']): options['lastfilePath'] = '/'
        self.filepath = filedialog.asksaveasfilename(initialdir=options['lastfilePath'], title="Select file",
                                                     filetypes=(("pdf files", "*.pdf"), ("all files", "*.*")))
        self.displayWindow.focus_force()
        if self.filepath:
            options['lastFile'] = self.filepath
            options['lastfilePath'] = os.path.dirname(self.filepath)
            self.saveOptions(options)
            self.updatestatusBar('Saving...')
            self.doc.save(self.filepath)
            self.updatestatusBar('Saved')
            self.displayWindow.title(os.path.basename(self.filepath))

    def save(self):
        self.readTree()
        if self.doc:
            if self.doc.can_save_incrementally():
                self.updatestatusBar('Saving...')
                self.doc.saveIncr()
                self.updatestatusBar('Saved')
            else:
                self.filepath = filedialog.asksaveasfilename(initialdir=self.options['lastfilePath'], title="Select file",
                                                           filetypes=(("pdf files", "*.pdf"), ("all files", "*.*")))
                self.displayWindow.focus_force()
                if self.filepath:
                    self.updatestatusBar('Saving...')
                    self.doc.save(self.filepath)
                    self.updatestatusBar('Saved')

    def printPDF(self):
        printDialog(self.displayWindow,self.doc)

    def on_closing_options(self):
        self.options['oGeo']=self.optionsWindow.geometry()
        self.saveOptions(self.options)
        self.optionsWindow.destroy()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # check for save doc
            options = self.loadOptions()
            options['mGeo'] = self.displayWindow.geometry()
            self.saveOptions(options)
            if self.doc: self.doc.close()
            self.displayWindow.destroy()

    def refreshallPages(self):
        self.dlist_tab = [None] * self.doc.page_count
        self.displayPage()

    def refreshPage(self, pg=None):
        if not self.doc: return
        if not pg: pg=self.cur_page
        self.dlist_tab[pg]=None
        self.displayPage()

    def scaleChange(self,v):
        pg=int(v)-1
        if pg is None:
            pg = self.cur_page
        self.cur_page = pg
        self.setPgDisplay()

    def setPage(self,pg=None):
        #sets the page to pg
        if pg is None:
            pg=self.cur_page
        self.cur_page=pg
        self.vbar.set(self.cur_page+1) #this triggers scaleChange

    def insertPages(self, pagesPDF, pg):
        if self.doc==None: return

        def add_default_label(doc):
            labels=doc.get_labels_rule_dict()
            if len(labels) == 0:  # if no labels create default one
                labels.append({'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1})
            doc.set_page_labels(labels)

        def which_label_have_we_split(doc):
            #returns the index of label we have split
            return_lb=-1
            for lb in doc.get_labels_rule_dict():
                if lb['startpage']>=pg: return return_lb
                return_lb+=1
            return return_lb

        def getendpageLb(doc,index):
            #returns end page of this label[index]
            Lbs=doc.get_labels_rule_dict()
            if index+1<len(Lbs):
                return Lbs[index+1]['startpage']
            else:
                return doc.page_count

        def getnewPgLabels(pagesPDF):
            newLbs=pagesPDF.get_labels_rule_dict()
            #All the mew labels have to be increased by the pgNo insert point, pg
            for lb in newLbs: lb['startpage']+=pg
            oldLbs=self.doc.get_labels_rule_dict()
            split_lb=which_label_have_we_split(self.doc)
            for i in range(split_lb+1, len(oldLbs)): oldLbs[i]['startpage']+=pagesPDF.page_count
            if split_lb>-1:
                end_pg=getendpageLb(self.doc,split_lb)
                pgs_left_in_split_lb=end_pg-pg
                if pgs_left_in_split_lb>0:
                    new_lb=oldLbs[split_lb]
                    new_lb['startpage']=end_pg+pagesPDF.page_count
                    oldLbs.append(new_lb)

            newLbs.extend(oldLbs)
            #sort them
            newLbs.sort(key=lambda x: x["startpage"])
            return newLbs

        def adjustTOC(addPg,no_pages):
            def search_tree(node):
                for child_node in self.tree.get_children(node):
                    pg=self.tree.item(child_node)['values'][2]-1
                    if pg>=addPg:
                        pg+=no_pages
                    pgLbl=self.doc[pg].get_label()
                    self.tree.set(child_node,1,pgLbl)
                    self.tree.set(child_node,2,pg+1)
                    self.mirrorinChronoTree(child_node)
                    if self.tree.get_children(child_node):
                        search_tree(child_node)
            search_tree("")

        self.doc.add_default_label()
        pagesPDF.add_default_label()
        newLbs=getnewPgLabels(pagesPDF)
        self.doc.insertPDF(docsrc=pagesPDF,start_at=pg)
        self.doc.set_page_labels(newLbs)
        adjustTOC(pg,pagesPDF.page_count)

        for i in range(0,pagesPDF.page_count): self.dlist_tab.insert(pg,None)

        if self.cur_page >= self.doc.page_count: self.cur_page = self.doc.page_count - 1
        self.vbar.config(to=self.doc.page_count)

        self.pgCountTxt.set("/ " + str(self.doc.page_count))

        self.displayPage()


    def rotateDialog(self):
        rotateDialog(self.displayWindow,self, self.doc[self.cur_page].get_label())

    def rotate(self, degrees, pgRange=None, addHistory=True):
        if self.doc:
            if not pgRange: pgRange=str(self.doc[0].get_label())+ "-" + str(self.doc[self.doc.page_count-1].get_label())
            a= self.doc.parse_page_string(pgRange)
            if a:
                for pgNo in a:
                    page=self.doc[pgNo]
                    page.setRotation(page.rotation+degrees)
                    self.dlist_tab[pgNo]=None
            self.displayPage()
            if addHistory: self.adddocHistory({'code': "DOC_rotation", 'pgRange':pgRange,'degrees': degrees})


    def deletePage(self, pg=None, addHistory=True):
        if self.doc==None: return
        deletePgNo=pg
        if not deletePgNo: deletePgNo=self.cur_page

        def adjustPgLabels(delPg):
            newlbs=[]
            for l in self.doc.get_labels_rule_dict():
                if delPg<l['startpage']: l['startpage']-=1
                newlbs.append(l)
            self.doc.set_page_labels(newlbs)

        def adjustTOC(delPg):
            def search_tree(node):
                for child_node in self.tree.get_children(node):
                    pg=self.tree.item(child_node)['values'][2]-1
                    if pg>delPg: pg-=1
                    pgLbl=self.doc[pg].get_label()
                    self.tree.set(child_node,1,pgLbl)
                    self.tree.set(child_node,2,pg+1)
                    self.mirrorinChronoTree(child_node)
                    if self.tree.get_children(child_node):
                        search_tree(child_node)
            search_tree("")

        if deletePgNo>=0 and deletePgNo<self.doc.page_count:
            deletedPagePdf=fitz.open()
            deletedPagePdf.insertPDF(self.doc,from_page=deletePgNo, to_page=deletePgNo)
            self.doc.deletePage(deletePgNo)
            adjustPgLabels(deletePgNo)
            adjustTOC(deletePgNo)
            self.dlist_tab.pop(deletePgNo)
            if addHistory: self.adddocHistory({'code':"DOC_pageDeleted", "page": deletedPagePdf, 'pgNo': deletePgNo})

        if self.cur_page >= self.doc.page_count: self.cur_page = self.doc.page_count - 1
        self.vbar.config(to=self.doc.page_count)

        self.pgCountTxt.set("/ " + str(self.doc.page_count))

        self.displayPage()

    def displayPage(self):
        if not self.doc: return
        page=self.doc[self.cur_page]
        if not TC.isTOCPage(page):
            page.remove_draw_links()
            page.draw_links()
        self.img, self.clip_pos = self.get_page(self.cur_page)
        self.canvas.delete('all')
        w=(self.canvas.winfo_width()-self.img.width())/2
        h=(self.canvas.winfo_height()-self.img.height())/2
        self.imageid=self.canvas.create_image(w,h, anchor=tk.NW, image=self.img)
        self.displayWindow.update_idletasks()

    def setPgDisplay(self):
        if not self.doc:
            self.pgEntry.delete(0, tk.END)
            self.pgLabelEntry.delete(0, tk.END)
            self.pgCountTxt.set("/ ")
            return
        pgTxt=str(self.cur_page+1)
        pgLblTxt=self.doc[self.cur_page].get_label()
        self.pgCountTxt.set("/ " + str(self.doc.page_count))
        self.pgEntry.delete(0,tk.END)
        self.pgEntry.insert(0,pgTxt)
        self.pgLabelEntry.delete(0,tk.END)
        self.pgLabelEntry.insert(0,pgLblTxt)
        self.displayPage()
        self.loadthumbNails()

    def LbStrChanged(self, event):
        str=self.pgLabelEntry.get()
        if len(self.doc.get_page_numbers(str))>0:
            self.cur_page=self.doc.get_page_numbers(str)[0]
            self.addpageHistory(self.cur_page)
        self.setPage()

    def pgStrChanged(self, event):
        str=self.pgEntry.get()
        if str.isnumeric():
            if int(str)>=0 and int(str)<=self.doc.page_count:
                self.cur_page=int(str)-1
                self.addpageHistory(self.cur_page)
        self.setPage()

    def get_page(self, pno, clip=None, zoom=False, max_size=None):
        """Return a PNG image for a document page number.
        """
        dlist = self.dlist_tab[pno]  # get display list of page number
        if not dlist:  # create if not yet there
            self.dlist_tab[pno] = self.doc[pno].get_displaylist()
            dlist = self.dlist_tab[pno]
        r = dlist.rect  # the page rectangle
        if not clip: clip = r
        # ensure image fits screen:
        # exploit, but do not exceed width or height
        if not max_size:
            max_size=(self.canvas.winfo_width(),self.canvas.winfo_height())
        max_width=max_size[0]
        max_height=max_size[1]

        zoom_0 = min(1, max_width / r.width, max_height / r.height)
        if zoom_0 == 1:
            zoom_0 = min(max_width / r.width, max_height/ r.height)
        mat_0 = fitz.Matrix(zoom_0, zoom_0)

        if not zoom:  # show total page
            pix = dlist.get_pixmap(matrix=mat_0, alpha=False)
        else:
#            mp = r.tl + (r.br - r.tl) * 0.5  # page rect center
#            w2 = r.width / 2
#            h2 = r.height / 2
#            clip = r * 0.5
#            tl = zoom[0]  # old top-left
#            tl.x += zoom[1] * (w2 / 2)
#            tl.x = max(0, tl.x)
#            tl.x = min(w2, tl.x)
#            tl.y += zoom[2] * (h2 / 2)
#            tl.y = max(0, tl.y)
#            tl.y = min(h2, tl.y)
#            clip = fitz.Rect(tl, tl.x + w2, tl.y + h2)

            mat = mat_0 * fitz.Matrix(2, 2)  # zoom matrix
            pix = dlist.get_pixmap(alpha=False, matrix=mat, clip=clip)

#        if first:  # first call: tkinter still inactive
#            img = pix.getPNGData()  # so use fitz png output
#        else:  # else take tk photo image
#            pilimg = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
#            img = ImageTk.PhotoImage(pilimg)

        pix1 = fitz.Pixmap(pix, 0) if pix.alpha else pix
        imgdata = pix1.tobytes('ppm')
        tkimg = tk.PhotoImage(data=imgdata)

        self.width=pix1.width
        self.height=pix1.height

        return tkimg, clip.tl  # return image, clip position

    def ocr(self):
        ocrmypdf.ocr(self.filepath, self.filepath+"_", deskew=True)
        pass

    def convertpageRect(self, rect):
        #converts a fitz.rect on the page to a rect on the pixmap
        pointA=self.convertpagePoint(rect.top_left)
        pointB=self.convertpagePoint(rect.bottom_right)
        return fitz.Rect(pointA, pointB)

    def convertpagePoint(self,point):
        #converts a fitz.point on the page to a point on the pixmap
        if not self.doc: return None
        page=self.doc[self.cur_page]
        c=self.canvas.coords(self.imageid) #gives TL of image
        xFactor=self.width/page.rect.width
        yFactor=self.height/page.rect.height
        rtnPoint=fitz.Point((point[0]*xFactor)+c[0], (point[1]*yFactor)+c[1])
        return rtnPoint

    def convertcanvasPointtoPDFpoint(self, point):
        # converts a fitz.point on the page to a point on the pixmap
        if not self.doc: return None
        page = self.doc[self.cur_page]
        c = self.canvas.coords(self.imageid)  # gives TL of image
        xFactor = self.width / page.rect.width
        yFactor = self.height / page.rect.height
        rtnPoint = fitz.Point((point[0] - c[0]) / xFactor, (point[1] - c[1]) / yFactor)
        return rtnPoint

    def pointInRect(self, point, rect):
        # where x and y are coordinates of click
        x1, y1, x2, y2 = rect
        x, y = point
        if (x1 < x and x < x2):
            if (y1 < y and y < y2):
                return True
        return False

    def link_clicked(self,point):
        if not self.doc: return None
        page=self.doc[self.cur_page]
        lnks = page.get_links()
        for lnk in lnks:
            if self.pointInRect(point, self.convertpageRect(lnk['from'])):
                self.action_link(lnk)
                return lnk
        return None

    def action_link(self,lnk):
        if lnk == None: return
        page=self.doc[self.cur_page]
        kind = lnk['kind']
        if kind == 1:
            # go to a page in this document
            self.addpageHistory(lnk['page'])
            self.setPage(lnk['page'])
        if kind == 2:
            # go to url
            url = lnk['uri']
            webbrowser.open(url, new=0, autoraise=True)
        if kind == 5:
            filepath = lnk['file']
            pg = lnk['page']
            cl=self.alreadyOpen(filepath)
            if cl:
                cl.setPage(pg)
            else:
                newCl=display(tk.Toplevel(), filepath).setPage(pg)
                openFiles[newCl.id]={'filepath':filepath, 'class': newCl}
#            if not already_in_list(fname): add_to_list(fname)  # add to list if not already there
#            self.dict[fname]['pg'] = pg
#            setup_newdoc_display(fname)

    def alreadyOpen(self,filepath):
        for f in openFiles:
            if openFiles[f]['filepath']==filepath: return openFiles[f]['class']
        return None

    def adddocHistory(self, options):
        if not self.doc: return
        self.docHistory=self.docHistory[0:self.docHistoryIndex+1]
        self.docHistory.append(options) #add doc to history
        self.docHistoryIndex=len(self.docHistory)-1 #adjust index for new length of history

    def addpageHistory(self,pg):
        #first we need to chop off any surplus
        if not self.doc: return
        #check new pg is different from last page
        if not pg==self.pageHistory[self.pageHistoryIndex]:
            self.pageHistory=self.pageHistory[0:self.pageHistoryIndex+1]
            self.pageHistory.append(pg) #add page to history
            self.pageHistoryIndex=len(self.pageHistory)-1 #adjust index for new length of history

    def undo(self):
        #equivalent to decrementing history
        if not self.doc: return
        if self.docHistoryIndex<0 and self.docHistoryIndex>len(self.docHistory)-1:
            return
        options=self.docHistory[self.docHistoryIndex]
        if options:
            if options['code']=="TOC_addedItem":
                if self.tree.exists(options['id']):
                    self.tree.delete(options['id'])
                    self.chronotree.delete(options['id'])
                    self.readTree()
            if options['code']=="TOC_textChange":
                if self.tree.exists(options['id']):
                    self.tree.item(options['id'], text=options['old_text'])
                    self.mirrorinChronoTree(options['id'])
                    self.readTree()
            if options['code']=="TOC_dateChange":
                if self.tree.exists(options['id']):
                    self.tree.set(options['id'],0,options['old_date'])
                    self.mirrorinChronoTree(options['id'], sort=True)
                    self.readTree()
            if options['code']=="TOC_pgLabelChange":
                if self.tree.exists(options['id']):
                    self.tree.set(options['id'],1,options['old_pgLabel'])
                    self.tree.set(options['id'],2,options['old_pgNo'])
                    self.mirrorinChronoTree(options['id'])
                    self.readTree()
            if options['code']=="TOC_pgChange":
                if self.tree.exists(options['id']):
                    self.tree.set(options['id'],1,options['old_pgLabel'])
                    self.tree.set(options['id'],2,options['old_pgNo'])
                    self.mirrorinChronoTree(options['id'])
                    self.readTree()
            if options['code']=="TOC_deletedItem":
                for s in reversed(options['selectedList']):
                    self.tree.insert(s['parentID'], s['locus'], iid=s['id'], text=s['text'], values=s['values'], tags=s['tags'])
                    self.mirrorinChronoTree(s['id'])
                    for l in s['deleteList']:
                        self.tree.insert(l['parentID'], l['locus'], iid=l['id'], text=l['text'], values=l['values'], tags=l['tags'])
                        self.mirrorinChronoTree(l['id'])
                self.chronotree.sort()
                self.readTree()
            if options['code']=="TOC_tagChanged":
                for s in options['selectedList']:
                    if self.tree.exists(s['id']): self.tree.item(s['id'],tags=s['old_tags'])
                    self.mirrorinChronoTree(s['id'])
                self.readTree()
            if options['code']=='TOC_moveditem':
                self.tree.move(options['id'], options['fr']['parent'], options['fr']['index'])
                self.tree.glueNodes(self.tree.gluedNodes)
                self.readTree()
            if options['code']=="TOC_sorted":
                self.doc.set_toc(options['old_toc'])
                self.fillTree()
            if options['code']=="TOC_changeddestination":
                for s in options['selectedList']:
                    pgLb=self.doc[s['old_page']].get_label()
                    self.tree.set(s['id'],1,pgLb)
                    self.tree.set(s['id'],2,s['old_page'])
                    self.mirrorinChronoTree(s['id'])
                self.readTree()
            if options['code']=="DOC_pageDeleted":
                self.insertPages(options['page'], options['pgNo'])
            if options['code']=="DOC_rotation":
                self.rotate(degrees=-options['degrees'],pgRange=options['pgRange'],addHistory=False)
            if options['code']=="DOC_paginated":
                PG.remove_pagination(self.doc,options['options'],self, addHistory=False)
                self.displayPage()
            if options['code']=="DOC_pagination_removed":
                PG.paginate(self.doc,options['options'],self, addHistory=False)
                self.displayPage()
            if options['code']=='DOC_addtoc':
                TC.delete_toc(doc=self.doc, display=self, addHistory=False)
                self.setPgDisplay()
            if options['code']=='DOC_deletetoc':
                TC.write_toc(doc=self.doc, options=options['options'], display=self, addHistory=False)
                self.setPage(0)
            if options['code']=='DOC_highlight':
                self.setPage(options['annot'].pg)
                page=self.doc[options['annot'].pg]
                page.deleteAnnot(page.loadAnnot(options['annot'].annotxref))
                self.refreshPage()
            if options['code']=='DOC_deletehighlight':
                fitz.TOOLS.set_annot_stem(annot_name + 'highlight')
                for s in options['annots']:
                    oldannotxref=s.annotxref
                    page=self.doc[s.pg]
                    newannot=page.addHighlightAnnot(s.quads)
                    newannot.setColors({'stroke': s.colour})
                    newannot.update()
                    self.swapnewforoldannotref(s.pg, newannot.xref,oldannotxref)
                self.refreshPage()


            self.docHistoryIndex -= 1

    def mirrorinChronoTree(self,id, sort=False):
        dt=getdatefromText(', '+self.tree.item(id)['values'][0])
        dy=getdayofWeek(dt)
        if self.chronotree.exists(id):
            if dt:
                self.chronotree.item(id, text=self.tree.item(id)['values'][0]) #date
                self.chronotree.set(id, 0, dy) #day
                self.chronotree.set(id, 1, self.tree.item(id)['text']) #text
                self.chronotree.set(id, 2, self.tree.item(id)['values'][1]) #Page Label
                self.chronotree.set(id, 3, self.tree.item(id)['values'][2]) #Page
                self.chronotree.item(id,tags=self.tree.item(id)['tags'])
                if sort: self.chronotree.sort()
            else:
                self.chronotree.delete(id)
        else:
            if dt:
                #need to add to chronoTree
                self.chronotree.insert('','end',iid=id)
                self.chronotree.item(id, text=self.tree.item(id)['values'][0]) #date
                self.chronotree.set(id, 0, dy) #day
                self.chronotree.set(id, 1, self.tree.item(id)['text']) #text
                self.chronotree.set(id, 2, self.tree.item(id)['values'][1]) #Page Label
                self.chronotree.set(id, 3, self.tree.item(id)['values'][2]) #Page
                self.chronotree.item(id,tags=self.tree.item(id)['tags'])
                if sort: self.chronotree.sort()



    def redo(self):
        #equivalent to incrementing history
        if not self.doc: return
        self.docHistoryIndex+=1
        if self.docHistoryIndex>=len(self.docHistory):
            self.docHistoryIndex=len(self.docHistory)-1
            return #nothing futher to redo
        options=self.docHistory[self.docHistoryIndex]
        if options:
            if options['code']=="TOC_addedItem":
                self.tree.insert(options['parentID'], options['locus'], iid=options['id'], text=options['text'], values=options['values'])
                self.mirrorinChronoTree(options['id'])
                self.readTree()
            if options['code']=="TOC_textChange":
                if self.tree.exists(options['id']):
                    self.tree.item(options['id'], text=options['text'])
                    self.mirrorinChronoTree(options['id'])
                    self.readTree()
            if options['code']=="TOC_dateChange":
                if self.tree.exists(options['id']):
                    self.tree.set(options['id'], 0, options['date'])
                    self.mirrorinChronoTree(options['id'], sort=True)
                    self.readTree()
            if options['code']=="TOC_pgLabelChange":
                if self.tree.exists(options['id']):
                    self.tree.set(options['id'],1,options['pgLabel'])
                    self.tree.set(options['id'],2,options['pgNo'])
                    self.mirrorinChronoTree(options['id'])
                    self.readTree()
            if options['code']=="TOC_pgChange":
                if self.tree.exists(options['id']):
                    self.tree.set(options['id'],1,options['pgLabel'])
                    self.tree.set(options['id'],2,options['pgNo'])
                    self.mirrorinChronoTree(options['id'])
                    self.readTree()
            if options['code']=="TOC_deletedItem":
                for s in options['selectedList']:
                    if self.tree.exists(s['id']):
                        self.tree.delete(s['id'])
                        if self.chronotree.exists(s['id']):
                            self.chronotree.delete(s['id'])
                self.readTree()
            if options['code']=="TOC_tagChanged":
                for s in options['selectedList']:
                    self.tree.item(s['id'],tags=s['tags'])
                    self.mirrorinChronoTree(s['id'])
                self.readTree()
            if options['code']=='TOC_moveditem':
                self.tree.move(options['id'], options['to']['parent'], options['to']['index'])
                self.tree.glueNodes(self.tree.gluedNodes)
                self.readTree()
            if options['code']=="TOC_sorted":
                self.doc.set_toc(options['new_toc'])
                self.fillTree()
            if options['code']=="TOC_changeddestination":
                for s in options['selectedList']:
                    pgLb=self.doc[s['new_page']].get_label()
                    self.tree.set(s['id'],1,pgLb)
                    self.tree.set(s['id'],2,s['new_page'])
                    self.mirrorinChronoTree(s['id'])
                self.readTree()
            if options['code']=="DOC_pageDeleted":
                self.deletePage(options['pgNo'], addHistory=False)
            if options['code']=="DOC_rotation":
                self.rotate(degrees=options['degrees'],pgRange=options['pgRange'], addHistory=False)
            if options['code']=="DOC_paginated":
                PG.paginate(self.doc,options['options'],self, addHistory=False)
                self.displayPage()
            if options['code']=="DOC_pagination_removed":
                PG.remove_pagination(self.doc,options['options'],self, addHistory=False)
                self.displayPage()
            if options['code']=='DOC_addtoc':
                TC.write_toc(doc=self.doc, options=options['options'], display=self, addHistory=False)
                self.setPage(0)
            if options['code']=='DOC_deletetoc':
                TC.delete_toc(doc=self.doc, display=self, addHistory=False)
                self.setPgDisplay()
            if options['code']=='DOC_highlight':
                fitz.TOOLS.set_annot_stem(annot_name + 'highlight')
                self.setPage(options['annot'].pg)
                page=self.doc[options['annot'].pg]
                oldannotxref=options['annot'].annotxref
                newannot = page.addHighlightAnnot(options['annot'].quads)
                newannot.setColors({'stroke': options['annot'].colour})
                newannot.update()
                self.swapnewforoldannotref(options['annot'].pg, newannot.xref,oldannotxref)
                self.refreshPage()
            if options['code']=='DOC_deletehighlight':
                for s in options['annots']:
                    page=self.doc[s.pg]
                    page.deleteAnnot(page.loadAnnot(s.annotxref))
                self.refreshPage()

    def swapnewforoldannotref(self, pg, newannotxref,oldannotxref):
        for x in self.docHistory:
            if x:
                if x['code']=='DOC_deletehighlight':
                    for s in x['annots']:
                        if s.annotxref == oldannotxref and s.pg==pg:
                            s.annotxref = newannotxref
                if x['code'] == 'DOC_highlight':
                    if x['annot'].annotxref == oldannotxref and x['annot'].pg==pg:
                        x['annot'].annotxref = newannotxref


    def dechistPg(self):
        if not self.doc: return
        self.pageHistoryIndex-=1
        if self.pageHistoryIndex<0:
            self.pageHistoryIndex=len(self.pageHistory)-1
        self.cur_page=self.pageHistory[self.pageHistoryIndex]
        self.setPage()

    def inchistPg(self):
        if not self.doc: return
        self.pageHistoryIndex+=1
        if self.pageHistoryIndex>=len(self.pageHistory):
            self.pageHistoryIndex=0
        self.cur_page=self.pageHistory[self.pageHistoryIndex]
        self.setPage()

    def decPg(self):
        if not self.doc: return
        self.cur_page -=1
        if self.cur_page<0:
            self.cur_page=self.doc.page_count-1
        self.addpageHistory(self.cur_page)
        self.setPage()

    def incPg(self):
        if not self.doc: return
        self.cur_page +=1
        if self.cur_page>=self.doc.page_count:
            self.cur_page=0
        self.addpageHistory(self.cur_page)
        self.setPage()

    def gofirstPage(self):
        print('go first page')
        if not self.doc: return
        self.cur_page=0
        self.addpageHistory(self.cur_page)
        self.setPage()

    def golastPage(self):
        print('go last page')
        if not self.doc: return
        self.cur_page=self.doc.page_count-1
        self.addpageHistory(self.cur_page)
        self.setPage()

    def resize(self, event):
        self.refreshPage()

    def loadmaintoolBar(self):
        # Toolbar
        toolbar = tk.Frame(self.displayWindow, bd=1, relief=tk.RAISED)

        #File buttons
        fileFrame=tk.Frame(toolbar, bd=1, relief=tk.RAISED)
        fileFrame.pack(side=tk.LEFT, padx=10)
        # Open button
        img = Image.open(open_location)
        eimg = ImageTk.PhotoImage(img)
        openButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.openFile())
        openButton.image = eimg
        openButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(openButton, 'Open')
        # Save button
        img = Image.open(save_location)
        eimg = ImageTk.PhotoImage(img)
        saveButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.save())
        saveButton.image = eimg
        saveButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(saveButton, 'Save')
        # Print button
        img = Image.open(print_location)
        eimg = ImageTk.PhotoImage(img)
        printButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.printPDF())
        printButton.image = eimg
        printButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(printButton, 'Print')
        # Close button
        img = Image.open(close_location)
        eimg = ImageTk.PhotoImage(img)
        exitButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.closeFile())
        exitButton.image = eimg
        exitButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(exitButton, 'Close')

        #Navigation buttons
        navigationFrame=tk.Frame(toolbar, bd=1, relief=tk.RAISED)
        navigationFrame.pack(side=tk.LEFT, padx=10)
        # Left button
        img = Image.open(left_location)
        eimg = ImageTk.PhotoImage(img)
        self.leftButton = tk.Button(navigationFrame, image=eimg, relief=tk.FLAT, command=lambda: self.decPg())
        self.leftButton.image = eimg
        self.leftButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(self.leftButton, 'Back a page')
        #Page Label
        self.pgLabelEntry=tk.Entry(navigationFrame, width=5, justify='center')
        self.pgLabelEntry.bind("<FocusOut>", self.LbStrChanged)
        self.pgLabelEntry.bind("<Return>", self.LbStrChanged)
        self.pgLabelEntry.bind("<KP_Enter>", self.LbStrChanged)
        self.pgLabelEntry.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(self.pgLabelEntry, 'Page label')
        #Page
        self.pgEntry=tk.Entry(navigationFrame, width=5, justify='center')
        self.pgEntry.bind("<FocusOut>", self.pgStrChanged)
        self.pgEntry.bind("<Return>", self.pgStrChanged)
        self.pgEntry.bind("<KP_Enter>", self.pgStrChanged)
        self.pgEntry.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(self.pgEntry, 'Page')
        #Number of pages
        self.pgCountTxt=tk.StringVar()
        self.pgCountLabel=tk.Label(navigationFrame, width=5,justify='center', textvariable=self.pgCountTxt)
        self.pgCountLabel.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(self.pgCountLabel, 'Page count')
        # Right button
        img = Image.open(right_location)
        eimg = ImageTk.PhotoImage(img)
        self.rightButton = tk.Button(navigationFrame, image=eimg, relief=tk.FLAT, command=lambda: self.incPg())
        self.rightButton.image = eimg
        self.rightButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(self.rightButton, 'Forward a page')

        #Other tools
        otherFrame=tk.Frame(toolbar, bd=1, relief=tk.RAISED)
        otherFrame.pack(side=tk.LEFT, padx=10)
        # Pagination button
        img = Image.open(book_location)
        eimg = ImageTk.PhotoImage(img)
        paginationButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.paginate())
        paginationButton.image = eimg
        paginationButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(paginationButton, 'Paginate')
        # Link button
        img = Image.open(link_location)
        eimg = ImageTk.PhotoImage(img)
        linkButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.addLinks())
        linkButton.image = eimg
        linkButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(linkButton, 'Hyperlink page references')
        # Order button
        img = Image.open(order_location)
        eimg = ImageTk.PhotoImage(img)
        orderButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.onOrder())
        orderButton.image = eimg
        orderButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(orderButton, 'Put pages in the order of the bookmarks')
        # Search button
        img = Image.open(search_location)
        eimg = ImageTk.PhotoImage(img)
        searchButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.searchText())
        searchButton.image = eimg
        searchButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(searchButton, 'Search text')
        # Delete button
        img = Image.open(delete_location)
        eimg = ImageTk.PhotoImage(img)
        deleteButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.deletePage())
        deleteButton.image = eimg
        deleteButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(deleteButton, 'Delete page')
        # anticlockwise button
        img = Image.open(anticlockwise_location)
        eimg = ImageTk.PhotoImage(img)
        rotateminusButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.rotate(degrees=-90, pgRange=self.doc[self.cur_page].get_label()))
        rotateminusButton.image = eimg
        rotateminusButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(deleteButton, 'Rotate anti-clockwise')
        # Clockwise button
        img = Image.open(clockwise_location)
        eimg = ImageTk.PhotoImage(img)
        rotateplusButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.rotate(degrees=90, pgRange=self.doc[self.cur_page].get_label()))
        rotateplusButton.image = eimg
        rotateplusButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(rotateminusButton, 'Rotate clockwise')
        # Options button
        img = Image.open(asterisk_location)
        eimg = ImageTk.PhotoImage(img)
        optionsButton = tk.Button(otherFrame, image=eimg, relief=tk.FLAT, command=lambda: self.ocr())
        optionsButton.image = eimg
        optionsButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(optionsButton, 'Options')

        #markup tools
        markupFrame=tk.Frame(toolbar, bd=1, relief=tk.RAISED)
        markupFrame.pack(side=tk.LEFT, padx=10)
        # Annotate button
        img = Image.open(book_location)
        eimg = ImageTk.PhotoImage(img)
        annotateButton = tk.Button(toolbar, image=eimg, relief=tk.FLAT, command=lambda: self.paginate())
        annotateButton.image = eimg
        annotateButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(annotateButton, 'Annotate')

        toolbar.pack(side=tk.TOP, fill=tk.X)

    def ontabChanged(self,event):
        print ('changed tab')
        index=self.tab_parent.index(self.tab_parent.select())
        if index==0:#i.e. the chrono tab is selected
            b=self.chronotree.selection()
            if len(b)>0:
                self.chronotree.selectSame(b[0])
        if index==1:#i.e. the chrono tab is selected
            b=self.tree.selection()
            if len(b)>0:
                self.tree.selectSame(b[0])
        self.loadthumbNails()
        self.displayWindow.update_idletasks()
        self.thumbnailCanvas.configure(scrollregion=self.thumbnailCanvas.bbox('all'),yscrollcommand=self.scroll_y.set)
        self.displayWindow.update_idletasks()
        pass

    def loadCanvas(self):

        #Create two tabs: one for 'Home' and one for 'Document'
        m=self.notebook=ttk.Notebook(self.displayWindow)
        m.pack(fill=tk.BOTH, expand=True)
        self.homeTab=ttk.Frame(self.notebook,relief=tk.FLAT)
        self.homeTab.pack(fill=tk.BOTH)
        self.notebook.add(self.homeTab, text='Home')
        self.docTab=ttk.Frame(self.notebook,relief=tk.FLAT)
        self.docTab.pack(fill=tk.BOTH)
        self.notebook.add(self.docTab, text='Doc')

        #The document tab
        m1=tk.PanedWindow(master=self.docTab, orient=tk.HORIZONTAL, showhandle=True)
        m1.pack(fill=tk.BOTH, expand=True)

        style=ttk.Style(root)
        style.configure('lefttab.TNotebook', tabposition='wn')

        self.tab_parent=ttk.Notebook(m1,style='lefttab.TNotebook')
        self.tab_parent.pack()
        m1.add(self.tab_parent)

        self.treeFrame=ttk.Frame(self.tab_parent,relief=tk.FLAT)
        self.chronoFrame=ttk.Frame(self.tab_parent, relief=tk.FLAT)
        self.thumbnailFrame=ttk.Frame(self.tab_parent, relief=tk.FLAT)

        # must keep a global reference to these two
        self.im1 = Image.open(bookmark_tab_location)
        self.ph1 = ImageTk.PhotoImage(self.im1)

        # must keep a global reference to these two
        self.im2 = Image.open(documents_location)
        self.ph2 = ImageTk.PhotoImage(self.im2)

        # must keep a global reference to these two
        self.im3 = Image.open(chrono_location)
        self.ph3 = ImageTk.PhotoImage(self.im3)

        self.tab_parent.add(self.treeFrame, image=self.ph1)
        self.tab_parent.add(self.chronoFrame, image=self.ph3)
        self.tab_parent.add(self.thumbnailFrame, image=self.ph2)

        self.thumbnailCanvas = tk.Canvas(self.thumbnailFrame)
        self.scroll_y = tk.Scrollbar(self.thumbnailFrame, orient=tk.VERTICAL, command=self.thumbnailCanvas.yview)
        self.scroll_y.pack(fill='y', side='right')

        self.frame = tk.Frame(self.thumbnailCanvas, borderwidth = 10)  # a sub frame for the thumbnail canvas
        self.frame.pack(expand=True,fill=tk.BOTH)
        self.loadthumbNailFrames()

        # put the frame in the canvas
        self.thumbnailCanvas.create_window(0, 0, anchor='nw', window=self.frame)
        # make sure everything is displayed before configuring the scrollregion
        self.thumbnailCanvas.update_idletasks()
        self.thumbnailCanvas.configure(scrollregion=self.thumbnailCanvas.bbox('all'),yscrollcommand=self.scroll_y.set)
        self.thumbnailCanvas.pack(fill='both', expand=True, side='left')
        self.scroll_y.pack(fill='y', side='right')


        #for the main view
        canvasFrame = tk.Frame(m1,bd=1,relief=tk.RAISED)
        m1.add(canvasFrame)

        #vertical slider
        self.vbar = tk.Scale(canvasFrame, orient=tk.VERTICAL, variable=self.sliderVar, command=self.scaleChange)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vbar.config(from_=1)


        self.canvas = tk.Canvas(canvasFrame)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.rubberBand=rubberBand(self.canvas,self)

        self.canvas.bind('<Configure>', self.resize)
        self.tab_parent.bind("<ButtonRelease-1>", self.ontabChanged)

    def loadmenuBar(self):
        # Menubar
        menubar = tk.Menu(self.displayWindow)
        self.displayWindow.config(menu=menubar)

        fileMenu=tk.Menu(menubar)
        menubar.add_cascade(label="File", underline=0, menu=fileMenu)
        fileMenu.add_command(label="Open...", accelerator='Command-o', underline=0, command=lambda: self.openFile())
        fileMenu.add_command(label="Merge...", accelerator='Command-m', underline=0, command=lambda: self.merge())
        fileMenu.add_command(label="Save", accelerator='Command-s', underline=0, command=lambda: self.save())
        fileMenu.add_command(label="Save as...", underline=0, command=lambda: self.saveAs())
        fileMenu.add_separator()  # Undo
        fileMenu.add_command(label="Undo...", accelerator='Command-z', underline=0, command=lambda: self.undo())
        fileMenu.add_command(label="Redo...", accelerator='Command-y', underline=0, command=lambda: self.redo())

        fileMenu.add_separator()  # Other
        fileMenu.add_command(label="Print...", accelerator='Command-p', underline=0, command=lambda: self.printPDF())
        fileMenu.add_separator()  # Other
        fileMenu.add_command(label="Close", accelerator='Command-w', underline=0, command=lambda: self.closeFile())
        fileMenu.add_command(label="Exit", underline=0, command=lambda: self.on_closing())

        self.toolsMenu = tk.Menu(menubar)
        menubar.add_cascade(label="Tools", underline=0, menu=self.toolsMenu)

        self.toolsMenu.add_command(label="Paginate...", command=lambda: self.paginateOptions())
        self.toolsMenu.add_command(label="Add TOC", command=lambda: self.addTOC())


        self.toolsMenu.add_command(label="Hyperlinking...", accelerator="Command-H", command=lambda: self.addLinks())


        self.toolsMenu.add_command(label="Search bookmarks...", accelerator="Command-f", command=lambda: self.searchDialog())
        self.toolsMenu.add_command(label="Search text...", accelerator="Shift-Command-f", command=lambda: self.searchText())

        self.toolsMenu.add_command(label="Rotate...", accelerator="Command-R", command=lambda: self.rotateDialog())


        self.toolsMenu.add_separator()  # Other
        self.toolsMenu.add_command(label="Options...", accelerator='Command-.', underline=0, command=lambda: self.onOptions())
        self.toolsMenu.add_separator()

    def loadchronotoolBar(self):
        # Toolbar
        self.chronoToolbar = tk.Frame(self.chronoFrame, bd=1, relief=tk.RAISED)
        #File buttons
        fileFrame=tk.Frame(self.chronoToolbar, bd=1, relief=tk.RAISED)
        fileFrame.pack(side=tk.LEFT)
        # Chrono button
        img = Image.open(table_location)
        eimg = ImageTk.PhotoImage(img)
        tocButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.addChrono())
        tocButton.image = eimg
        tocButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(tocButton, 'Chronology')

        # Search button
        img = Image.open(search_location)
        eimg = ImageTk.PhotoImage(img)
        autobookmarkButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.searchchronoDialog())
        autobookmarkButton.image = eimg
        autobookmarkButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(autobookmarkButton, 'Search bookmarks')

        # Target (set destination) button
        img = Image.open(target_location)
        eimg = ImageTk.PhotoImage(img)
        targetButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.setDestination())
        targetButton.image = eimg
        targetButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(targetButton, 'Set destination')

        self.chronoToolbar.pack(side=tk.TOP, fill=tk.X, pady=2)


    def loadbookmarktoolBar(self):
        # Toolbar
        self.bkToolbar = tk.Frame(self.treeFrame, bd=1, relief=tk.RAISED)
        #File buttons
        fileFrame=tk.Frame(self.bkToolbar, bd=1, relief=tk.RAISED)
        fileFrame.pack(side=tk.LEFT)
        # TOC button
        img = Image.open(table_location)
        eimg = ImageTk.PhotoImage(img)
        tocButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.addTOC())
        tocButton.image = eimg
        tocButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(tocButton, 'Table of Contents')
        # Autobookmark button
        img = Image.open(bookmark_location)
        eimg = ImageTk.PhotoImage(img)
        autobookmarkButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.autobookmark())
        autobookmarkButton.image = eimg
        autobookmarkButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(autobookmarkButton, 'Bookmark correspondence')

        # Search button
        img = Image.open(search_location)
        eimg = ImageTk.PhotoImage(img)
        autobookmarkButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.searchbookmarksDialog())
        autobookmarkButton.image = eimg
        autobookmarkButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(autobookmarkButton, 'Search/Replace bookmarks')

        # Target (set destination) button
        img = Image.open(target_location)
        eimg = ImageTk.PhotoImage(img)
        targetButton = tk.Button(fileFrame, image=eimg, relief=tk.FLAT, command=lambda: self.setDestination())
        targetButton.image = eimg
        targetButton.pack(side=tk.LEFT, padx=2, pady=2)
        CreateToolTip(targetButton, 'Set destination')



        self.bkToolbar.pack(side=tk.TOP, fill=tk.X, pady=2)


    def loadthumbNailFrames(self):
        widthLabel=200
        heightLabel=300
        labelsInRow=20 #int(self.thumbnailFrame.winfo_width()/widthLabel)
        labelsInCol=3 #int(self.thumbnailFrame.winfo_height()/heightLabel)
#        print(self.frame.winfo_width(), self.frame.winfo_height())
#        self.frame.config(width=self.thumbnailFrame.winfo_width(), height=self.thumbnailFrame.winfo_height())
#        print(self.frame.winfo_width(), self.frame.winfo_height())
        self.thumbnailButtons=[]
        for r in range(0,labelsInRow):
            for c in range(0,labelsInCol):
                buttonFrame=tk.Frame(self.frame)
                buttonFrame.width=200
                buttonFrame.height=300
#                buttonFrame.grid(row=r,column=c)
                buttonFrame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
                button = thumbnail(buttonFrame, 0, None, buttonFrame, self)
                button['text']='Hello'
                button.pack()
                self.thumbnailButtons.append(button)
        self.frame.pack()


    def loadthumbNails(self):
        return
        index=self.tab_parent.index(self.tab_parent.select())

        if index==2: #i.e. the thumbnail tab is selected
            print('loading thumbnails')
            count=0
            for button in self.thumbnailButtons:
                x, clip = self.get_page(self.cur_page+ count, max_size=(200,300))
                button.imageStore=x
                button['image']=x
                button['text']=self.doc[self.cur_page+count].get_label()
                button['compound']=tk.TOP
                button.buttonFrame['highlightbackground']='green'
                button.buttonFrame['highlightcolor']='green'
                button.page=self.cur_page+count
                button.buttonFrame['highlightthickness']=1 if button.page==self.cur_page else 0
                count+=1
        self.displayWindow.update_idletasks()

    def loadStatusBar(self):
        # Build status bar
        self.gstatus = tk.StringVar()
        self.gstatus.set('')
        self.statusBar = tk.Label(self.displayWindow, textvariable=self.gstatus, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusBar.pack(side=tk.BOTTOM, fill=tk.X)

    def loadProgressBar(self):
        # Build progress bar
        self.progressBar = ttk.Progressbar(self.displayWindow, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progressBar.pack(pady=10, side=tk.BOTTOM, fill=tk.BOTH)

    def updatestatusBar(self,status):
        self.gstatus.set(status)
        self.statusBar.update()

    def updateprogressBar(self, x):
        self.progressBar['value'] = x
        self.progressBar.update()

    def buildTrees(self):
        self.tree=treebookMarks(self.treeFrame,self)
        self.chronotree=treeChrono(self.chronoFrame,self)

    def emptyTree(self):
        self.tree.delete(*self.tree.get_children())
        self.chronotree.delete(*self.chronotree.get_children())

    def fillTree(self):
        t=time.time()
        self.tree.fillTree(self.chronotree)
#        self.tree['displaycolumns']=()
        e=time.time()
        print(e-t)

    def readTree(self):
        # Reads the treee and turns it into toc
        global tree, doc
        nTOC = []
        item={'index':0, 'colour': 'red', 'italic': True, 'bold': True}
        self.i=0
        colours=[]
        def search_tree(node, lvl):
            for child_node in self.tree.get_children(node):
                txt = self.tree.item(child_node)['text']
                dt = str(self.tree.item(child_node)['values'][0])
                if not dt == "":
                    txt = txt + ", " + dt
                pg = self.tree.item(child_node)['values'][2]
                #tags
                tags=self.tree.item(child_node)['tags']
                col=get_colour(tags)
                style=get_style(tags)
                italic=False
                bold=False
                plain=False
                if style=='italic': italic=True
                if style=='bold': bold=True
                if style=='plain': plain=True
                if not col==(0,0,0) or not style=='plain':
                    colours.append({'index':self.i, 'colour': col, 'italic':italic, 'bold': bold, 'plain': plain })
                nEntry = [lvl, txt, pg]
                nTOC.append(nEntry)
                self.i+=1
                if self.tree.get_children(child_node):
                    search_tree(child_node, lvl + 1)

        search_tree({}, 1)
        if self.doc:
            self.doc.set_toc(nTOC)  # replace table of contents
            #update those items that have a colour or a style
            toc=self.doc.get_toc(simple=False)
            for col in colours:
                d=toc[col['index']][3]
                d['color']=col['colour']
                d['italic']=col['italic']
                d['bold']=col['bold']
                self.doc.set_toc_item(col['index'],dest_dict=d)



    #search bookmark functions
    def searchbookmarksDialog(self):
        searchtreeDialogBookmarks(self.displayWindow, self.tree, self.chronotree, self)

    def searchchronoDialog(self):
        searchtreeDialogChrono(self.displayWindow, self.chronotree, self.tree, self)


    def setDestination(self):
        #set pg and page label of selected bookmarks to current page
        print('Setting destinations')
        pg=self.cur_page
        pgLbl=self.doc[pg].get_label()
        tab=self.tab_parent.index(self.tab_parent.select())
        if tab==0: #Bookmarks
            selection=self.tree.selection()
        elif tab==1: #Chrono
            selection=self.chronotree.selection()
        else: #neither
            return
        count=0
        selectedList=[]
        for s in selection:
            count+=1
            oldPg=self.tree.item(s)['values'][2]-1
            self.tree.set(s,1,pgLbl)
            self.tree.set(s,2,pg+1)
            newPg=pg
            selectedList.append({'id':s,'old_page':oldPg,'new_page':newPg})
            if self.chronotree.exists(s):
                self.chronotree.set(s,2,pgLbl)
                self.chronotree.set(s,3,pg+1)
        self.adddocHistory({'code':'TOC_changeddestination', 'selectedList': selectedList})
        self.readTree()
        self.updatestatusBar('Set destination for ' + str(count) + " items.")


    def searchText(self):
        if not self.doc: return
        searchtextDialog(self.displayWindow,self)


    def searchDialog(self):
        #search whichever tab is showing
        tab=self.tab_parent.index(self.tab_parent.select())
        if tab==0: #Bookmarks
            searchtreeDialogBookmarks(self.displayWindow, self.tree, self.chronotree, self)
        elif tab==1: #Chrono
            searchtreeDialogChrono(self.displayWindow, self.chronotree, self.tree, self)
        elif tab==2: #Thumbnails
            #change to tab 0 and search there
            self.tab_parent.select(0)
            searchtreeDialogBookmarks(self.displayWindow, self.tree, self.chronotree, self)
        else:
            #error
            sys.exit('Wrong tab number')

    #Other functions
    def paginateOptions(self):
        paginateDialog(self.displayWindow,self, self.doc[self.cur_page].get_label())


    def paginate(self):
        if self.doc:
            options = self.getpaginationOptions()
            self.reset()
            if PG.isPaginated(self.doc):
                PG.remove_pagination(self.doc, options, self)
                self.displayPage()
            else:
                PG.paginate(self.doc, options, self)
                self.displayPage()

    def addChrono(self):
        pass

    def addTOC(self):
        tocDialog(self.displayWindow,self)
        return
        if self.doc:
            options = self.loadOptions()
            options['margin'] = 25
            if TC.isTOC(self.doc, self):
                TC.delete_toc(self.doc, options)
            else:
                TC.write_toc(self.doc, options)
            self.reset()
        else:
            return

    def addLinks(self):
        if not self.doc: return
        dlg=hyperlinkDialog(self.displayWindow,self, self.doc[self.cur_page].get_label())

    def onOrder(self):
        self.readTree()
        if self.filepath:
            if self.doesFileExist(self.filepath):
                orderPages(self.doc, self)
                self.refresh()
                self.reset()

    def refresh(self):
        if self.filepath:
            if self.doesFileExist(self.filepath):
                self.fillTree()
                options = self.loadOptions()
                if PG.isPaginated(self.doc):
                    options['paginate'] = True
                    PG.paginate(self.doc, options, self)
                if TC.isTOC(self.doc, self):
                    options['margin'] = 25
                    TC.write_toc(doc, options,self)

    def onOptions(self):
        self.loadoptionsWindow()

    def loadoptionsWindow(self):
        # options window
        options = self.loadOptions()
        print (options)

        # deal with max-depth
        if self.doesFileExist(self.filepath):
            depthChoices = []
            doc = fitz.open(self.filepath)
            max_depth = TC.max_depth(doc)
            doc.close()
            for i in range(1, max_depth + 1): depthChoices.append(i)
        else:
            return

        # Main window
        optionsWindow = tk.Toplevel(self.displayWindow)

        def on_closing_options():
            options['oGeo'] = optionsWindow.geometry()
            self.saveOptions(options)
            optionsWindow.destroy()

        def onEscape(e):
            on_closing_options()

        optionsWindow.bind('<Key-Escape>', onEscape)


        optionsWindow.protocol("WM_DELETE_WINDOW", on_closing_options)
        optionsWindow.geometry(options['oGeo'])
        optionsWindow.grid_rowconfigure(0, weight=1)
        optionsWindow.grid_rowconfigure(1, weight=1)
        optionsWindow.grid_rowconfigure(2, weight=1)
        optionsWindow.grid_rowconfigure(3, weight=1)
        optionsWindow.grid_rowconfigure(4, weight=1)
        optionsWindow.grid_columnconfigure(0, weight=1)

        # Frames for Options
        # -- Pagination
        paginationFrame = tk.LabelFrame(optionsWindow, text="Pagination")
        paginationFrame.grid(row=0, padx=10, pady=10, sticky='NESW')
        textVarvPos = tk.StringVar(paginationFrame)
        textVarhPos = tk.StringVar(paginationFrame)
        textVarCol = tk.StringVar(paginationFrame)
        textVarSize = tk.StringVar(paginationFrame)
        # --Table of Contents
        tocFrame = tk.LabelFrame(optionsWindow, text="Table of Contents")
        tocFrame.grid(row=1, padx=10, pady=10,sticky='ew')
        textVarTitle = tk.StringVar()
        textVarDepth = tk.StringVar(tocFrame)
        # --Date options
        dtFrame = tk.LabelFrame(optionsWindow, text="Date options")
        dtFrame.grid(row=2, padx=10, pady=10,sticky='ew')
        textVarTitle = tk.StringVar()
        textVarDateFormat = tk.StringVar(dtFrame)
        # --Other
        otherFrame = tk.LabelFrame(optionsWindow, text="Other")
        otherFrame.grid(row=3, padx=10, pady=10,sticky='ew')
        textVarpgRange = tk.StringVar()
        # --Buttons
        buttonFrame = tk.Frame(optionsWindow)
        buttonFrame.grid(row=4, padx=10, pady=10,sticky='ew')

        # Vertical position
        trLabel = tk.Label(paginationFrame, text="Vertical Position:")
        trLabel.grid(row=0, column=0, sticky='W')
        choices = ['TOP', 'BOTTOM']
        verticalOption = tk.OptionMenu(paginationFrame, textVarvPos, *choices)
        verticalOption.grid(row=0, column=1, sticky="E")
        # Horizontal position
        trLabel = tk.Label(paginationFrame, text="Horizontal Position:")
        trLabel.grid(row=1, column=0, sticky='W')
        choices = ['LEFT', 'MIDDLE', 'RIGHT']
        horizontalOption = tk.OptionMenu(paginationFrame, textVarhPos, *choices)
        horizontalOption.grid(row=1, column=1, sticky='E')
        # Colour
        trLabel = tk.Label(paginationFrame, text="Colour:")
        trLabel.grid(row=0, column=2, sticky='W')
        choices = ['Black', 'Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Indigo', 'Violet']
        colourOption = tk.OptionMenu(paginationFrame, textVarCol, *choices)
        colourOption.grid(row=0, column=3, sticky='E')
        # Size
        trLabel = tk.Label(paginationFrame, text="Size:")
        trLabel.grid(row=1, column=2, sticky='W')
        choices = ['8', '12', '14', '16', '18', '20', '25', '30', '35', '40']
        sizeOption = tk.OptionMenu(paginationFrame, textVarSize, *choices)
        sizeOption.grid(row=1, column=3, sticky='E')

        # TOC
        # Title
        tocLabel = tk.Label(tocFrame, text="Title:")
        tocLabel.grid(row=0, column=0, sticky='w')
        tocEntry = tk.Entry(tocFrame, textvariable=textVarTitle)
        tocEntry.grid(row=0, column=1, columnspan=5, sticky='ew')
        # Depth
        trLabel = tk.Label(tocFrame, text="Depth:")
        trLabel.grid(row=1, column=0, sticky='w')
        depthOption = tk.OptionMenu(tocFrame, textVarDepth, *depthChoices)
        depthOption.grid(row=1, column=1, sticky='ew')

        # Date Format
        trLabel = tk.Label(dtFrame, text="Date format:")
        trLabel.grid(row=0, column=0, sticky='w')
        choices = ['DMY', 'MDY']
        dtOption = tk.OptionMenu(dtFrame, textVarDateFormat, *choices)
        dtOption.grid(row=0, column=1, sticky='ew')

        # Other
        pgrangeLabel = tk.Label(otherFrame, text="Page range:")
        pgrangeLabel.grid(row=0, column=0, sticky='w')
        pgrangeEntry = tk.Entry(otherFrame, textvariable=textVarpgRange)
        pgrangeEntry.grid(row=0, column=1, sticky='ew')

        cbdeleteLinks = ttk.Checkbutton(otherFrame, text="Delete existing links")
        cbdeleteLinks.state(['!alternate'])
        cbdeleteLinks.grid(row=1, column=0)

        def setDefault():
            defaultOptions = self.setdefaultOptions(None)
            setOptions(defaultOptions)

        def savetheseOptions(options):
            options['oGeo'] = optionsWindow.geometry()
            options['vPos'] = textVarvPos.get()
            options['hPos'] = textVarhPos.get()
            options['pgColour'] = textVarCol.get()
            options['pgSize'] = int(textVarSize.get())
            options['tocTitle'] = tocEntry.get()
            options['tocDepth'] = int(textVarDepth.get())
            options['pgRange'] = pgrangeEntry.get()
            options['deleteLinks'] = cbdeleteLinks.state()
            options['date'] = textVarDateFormat.get()
            self.saveOptions(options)

        def setOptions(options):
            # fill the gui
            textVarvPos.set(options['vPos'])
            textVarhPos.set(options['hPos'])
            textVarCol.set(options['pgColour'])
            textVarSize.set(options['pgSize'])
            textVarDateFormat.set(options['date'])

            textVarTitle.set(options['tocTitle'])
            if int(options['tocDepth']) > max_depth:
                options['tocDepth'] = str(max_depth)
            textVarDepth.set(options['tocDepth'])

            textVarpgRange.set(options['pgRange'])
            if 'selected' in options['deleteLinks']:
                cbdeleteLinks.state(['selected'])
            else:
                cbdeleteLinks.state(['!selected'])
            return

        def okClose():
            savetheseOptions(options)
            optionsWindow.destroy()

        setOptions(options)

        # Buttons
        defaultsButton = tk.Button(buttonFrame, text='DEFAULTS', command=lambda: setDefault())
        defaultsButton.grid(row=0, column=0)
        okButton = tk.Button(buttonFrame, text='OK', command=lambda: okClose())
        okButton.grid(row=0, column=1)


    #bookmark functions
    def autobookmark(self):
        if self.filepath and self.doc:
            if self.doesFileExist(self.filepath):
                AB.do(self.filepath, self.doc, self)
                self.fillTree()
            else:
                return
    #Options
    def loadOptions(self):
        options = {}
        try:
            shelf = shelve.open(settings_location)
            options = shelf["options"]
        finally:
#            shelf.close()
            self.setdefaultOptions(options)
            return options

    def gettocdefaultOptions(self):
        max_depth=0
        if self.doc:
            max_depth=self.doc.max_depth()
        options={'title': 'Table of Contents', 'maxDepth':max_depth}
        return options

    def gettocOptions(self):
        shelf = shelve.open(settings_location)
        if 'tocOptions' in shelf:
            return shelf['tocOptions']
        return self.gettocdefaultOptions()

    def savetocOptions(self, options):
        shelf = shelve.open(settings_location)
        shelf['tocOptions']=options
        shelf.close()



    def getpaginationdefaultOptions(self):
        options = {
            'HPOS': "R",
            'VPOS': 'B',
            'vMargin': 0.5,
            'hMargin': 0.5,
            'bBold': False,
            'bItalic': False,
            'Colour': 'Black',
            'fontName': 'Helvetica',
            'Size': 25,
            'All': True,
            'pgRange': None
        }
        return options

    def getpaginationOptions(self):
        shelf = shelve.open(settings_location)
        if 'pgOptions' in shelf:
            return shelf['pgOptions']
        return self.getpaginationdefaultOptions()

    def savepaginationOptions(self, options):
        shelf = shelve.open(settings_location)
        shelf['pgOptions']=options
        shelf.close()

    def saveOptions(self,options):
        try:
            shelf = shelve.open(settings_location)
            if options:
                shelf['options'] = options
            else:  # set defaults
                shelf['options'] = {'vPos': 'TOP', 'hPos': 'RIGHT', 'pgColour': 'RED', 'pgSize': 25,
                                    'tocTitle': "Contents",
                                    'tocDepth': 1, 'pgRange': "", 'deleteLinks': 1, 'date': 'DMY'}
        finally:
#            shelf.close()
            pass

    def setdefaultOptions(self,options):
        if options is None: options = {}
        # fill in any defaults
        if not 'lastFile' in options: options['lastFile'] = ""
        if not 'lastfilePath' in options: options['lastfilePath'] = "/"
        if not 'mGeo' in options: options['mGeo'] = '800x600'
        if not 'oGeo' in options: options['oGeo'] = '600x600'
        if not 'vPos' in options: options['vPos'] = "BOTTOM"
        if not 'hPos' in options: options['hPos'] = "RIGHT"
        if not 'pgColour' in options: options['pgColour'] = "RED"
        if not 'pgSize' in options: options['pgSize'] = 25
        if not 'tocTitle' in options: options['tocTitle'] = "Contents"
        if not 'tocDepth' in options: options['tocDepth'] = 1
        if not 'pgRange' in options: options['pgRange'] = ""
        if not 'deleteLinks' in options: options['deleteLinks'] = ('selected')
        if not 'lang' in options: options['date'] = ('DMY')
        return options

    def layout(self):
        #new window
        self.loadmenuBar()
        self.loadmaintoolBar()
        self.loadCanvas()
        self.loadbookmarktoolBar()
        self.loadchronotoolBar()
        self.buildTrees()
        self.loadStatusBar()
        self.loadProgressBar()
        self.setPgDisplay()
        self.loadthumbNails()
        self.configButtons()
        #bindings
#        self.leftButton.bind("<Shift-Button-1>", self.gofirstPage()) #doesn't work
#        self.rightButton.bind("<Shift-Button-1>", self.golastPage()) #doesn't work


openFiles={} #keep a dict of ids of open windows. Each window is a class display. Each entry openFiles[newCl.id]={'filepath':filepath, 'class': newCl}

root = tk.Tk()
root.title("PDFUtility")
root.geometry('800x600')
root.grid()
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

root.bind('<Configure>', full_screen)
# Escape bind to exit fullscreen.
root.bind('<Escape>', lambda e: root.attributes('-fullscreen', 0))

newCl=display(root)
openFiles[newCl.id] = {'filepath': "", 'class': newCl}

root.mainloop()













