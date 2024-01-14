import datetime
from utilities import configColours, configStyles, configHover, get_colour_name, converttoRGB
from wwc_page_labels import getpgLabelMapping
import sys
import tkinter as tk
import tkinter.ttk as ttk
import threading
from hyperlinkDialog import hyperlinkDialog
from wwc_parsebookmark import getdatefromText, getdatefromNode, gettextfromText, gettextpartDate, isValidDate, getdayofWeek, getsplit

class EntryPopup(tk.Entry):

    def __init__(self, parent, mirrorTree, iid, text, column, display, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.tv = parent
        self.iid = iid
        self.col = column
        self.display=display
        self.mirrorTree=mirrorTree

        self.insert(0, text)
        # self['state'] = 'readonly'
        # self['readonlybackground'] = 'white'
        # self['selectbackground'] = '#1BA1E2'
        self['exportselection'] = False

        self.focus_force()
        self.bind("<Return>", self.on_return)
        self.bind("<KP_Enter>", self.on_return)
        self.bind("<Tab>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Command-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())
        self.bind("<FocusOut>", lambda *ignore: self.destroy())

    def __del__(self):
        self.tv.focus_force()

    def on_return(self, event):
        sort=False
        if self.col == 0:
            oldText=self.tv.item(self.iid)['text']
            txt=self.get()
            if getdatefromText(txt):
                dtPt=gettextpartDate(txt)
                txtPt=gettextfromText(txt)
                self.tv.item(self.iid, text=txtPt)
                self.tv.set(self.iid, 0, dtPt)
            else:
                self.tv.item(self.iid, text=self.get())
            #if user has entered a date let's separate
            options = {'code': 'TOC_textChange', 'id': self.iid, 'text':txt, 'old_text':oldText}
            self.display.adddocHistory(options)

        else:
            if self.col == 1:
                # check this is a valid date
                settings = self.display.loadOptions()
                if isValidDate(self.get(), settings) or self.get()=="":
                    oldDate=self.tv.item(self.iid)['values'][0]
                    self.tv.set(self.iid, 0, self.get())
                    sort=True
                    options = {'code': 'TOC_dateChange', 'id': self.iid, 'date': self.get(), 'old_date': oldDate}
                    self.display.adddocHistory(options)

            if self.col == 2:  # i.e. page label
                # check page label exists
                if self.get() in self.display.dict:
                    oldpgLabel=self.tv.item(self.iid)['values'][self.col-1]
                    oldpgNo=self.tv.item(self.iid)['values'][2]
                    self.tv.set(self.iid, self.col - 1, self.get())
                    # need to change page
                    pg = self.display.dict[self.get()][0] + 1
                    self.tv.set(self.iid, 2, str(pg))
                    options = {'code': 'TOC_pgChange', 'id': self.iid, 'pgLabel': self.get(), 'old_pgLabel': oldpgLabel, 'pgNo': str(pg), 'old_pgNo':oldpgNo}
                    self.display.adddocHistory(options)
            if self.col == 3:  # i.e. page
                # fcheck page exists
                if self.get().isdigit():
                    pg = int(self.get()) - 1
                    if pg > -0 and pg < self.display.doc.page_count:
                        oldpgLabel=self.tv.item(self.iid)['values'][1]
                        oldpgNo=self.tv.item(self.iid)['values'][2]
                        self.tv.set(self.iid, self.col - 1, self.get())
                        # need to change page label
                        pgLbl = self.display.doc[pg].get_label()
                        self.tv.set(self.iid, 1, pgLbl)
                        options = {'code': 'TOC_pgChange', 'id': self.iid, 'pgLabel': pgLbl, 'old_pgLabel': oldpgLabel,
                                   'pgNo': self.get(), 'old_pgNo': oldpgNo}
                        self.display.adddocHistory(options)
        self.mirror(sort)
        self.destroy()
        self.display.readTree()
        self.display.tree.focus_set()

    def mirror(self):
        self.mirrorTree.item(self.iid, text=self.item(self.iid)['values'][1]) #text
        self.mirrorTree.item(self.iid)['values'][0]=self.item(self.iid)['text'] #Date
        self.mirrorTree.item(self.iid)['values'][1]=self.item(self.iid)['values'][2] #Page Label
        self.mirrorTree.item(self.iid)['values'][2]=self.item(self.iid)['values'][3] #Page

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # returns 'break' to interrupt default key-bindings
        return 'break'

class EntryPopupBookMark(EntryPopup):
    def mirror(self, sort=None):
        self.display.mirrorinChronoTree(self.iid,sort)

class EntryPopupChrono(EntryPopup):

    def mirror(self):
        if self.mirrorTree.exists(self.iid):
            self.mirrorTree.item(self.iid, text=self.tv.item(self.iid)['values'][1]) #text
            self.mirrorTree.set(self.iid,0, self.tv.item(self.iid)['text']) #date
            self.mirrorTree.set(self.iid,1,self.tv.item(self.iid)['values'][2]) #Page Label
            self.mirrorTree.set(self.iid,2,self.tv.item(self.iid)['values'][3]) #Page

    def on_return(self, event):
        if self.col == 0:
            # check this is a valid date
            settings = self.display.loadOptions()
            if isValidDate(self.get(), settings) or self.get() == "":
                oldDate=self.tv.item(self.iid)['text']
                self.tv.item(self.iid, text=self.get())
                dt = getdatefromText(', ' + self.get())
                dy = getdayofWeek(dt)
                self.tv.set(self.iid,0,dy)
                self.tv.sort()
                self.tv.see(self.iid)
                options = {'code': 'TOC_dateChange', 'id': self.iid, 'date': self.get(), 'old_date': oldDate}
                self.display.adddocHistory(options)
        else:
            if self.col==2: #i.e. text
                oldText=self.tv.item(self.iid)['values'][1]
                self.tv.set(self.iid, 1, self.get())
                options = {'code': 'TOC_textChange', 'id': self.iid, 'text':self.get(), 'old_text':oldText}
                self.display.adddocHistory(options)
            if self.col == 3:  # i.e. page label
                # check page label exists
                if self.get() in self.display.dict:
                    oldpgLabel=self.tv.item(self.iid)['values'][self.col-1]
                    oldpgNo=self.tv.item(self.iid)['values'][3]
                    self.tv.set(self.iid, self.col - 1, self.get())
                    # need to change page
                    pg = self.display.dict[self.get()][0] + 1
                    self.tv.set(self.iid, 3, str(pg))
                    options = {'code': 'TOC_pgChange', 'id': self.iid, 'pgLabel': self.get(), 'old_pgLabel': oldpgLabel,
                               'pgNo': str(pg), 'old_pgNo': oldpgNo}
                    self.display.adddocHistory(options)
            if self.col == 4:  # i.e. page
                # check page exists
                pg = int(self.get()) - 1
                if pg > -0 and pg < self.display.doc.page_count:
                    oldpgLabel=self.item(self.iid)['values'][2]
                    oldpgNo=self.item(self.iid)['values'][3]
                    self.tv.set(self.iid, self.col - 1, self.get())
                    # need to change page label
                    pgLbl = self.display.doc[pg].get_label()
                    self.tv.set(self.iid, 2, pgLbl)
                    options = {'code': 'TOC_pgChange', 'id': self.iid, 'pgLabel': pgLbl, 'old_pgLabel': oldpgLabel,
                               'pgNo': self.get(), 'old_pgNo': oldpgNo}
                    self.display.adddocHistory(options)
        self.mirror()
        self.destroy()
        self.display.readTree()
        self.display.chronotree.focus_set()

class EntryPopupMerge(EntryPopup):
    def mirror(self):
        pass

    def on_return(self, event):
        if self.col==1: #i.e. page range
            self.tv.set(self.iid, 0, self.get())
        if self.col == 4:  # i.e. bookmark label
            self.tv.set(self.iid, 3, self.get())
        self.destroy()


class treeClone(ttk.Treeview):
    def __init__(self, parent, display, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.editable=()
        self.display=display
        self.oldHoveredItem=None
        self.build()
        self.bindings()
        self.bind("<Control-a>", self.selectAll)
        self.bind("<Command-a>", self.selectAll)
        self.bind("<Shift-ButtonPress-2>", self.bshiftDown)

        self.headingEvents()
        self.setEditable()

        self.popup_menu=tk.Menu(self, tearoff=0)
        self.setcolourPopupCommands()
        self.setstylePopupCommands()
        self.setPopupCommands()

        #moving variables
        self.moving=False
        self.oldMovetoItem={'id':None, 'text':''}
        self.nodetoMove=None
        self.nodetoGoto=None
        self.nodetoGotoIndex=None
        self.currentText=""

        configColours(self)
        configStyles(self)
        configHover(self)

    def setcolourPopupCommands(self):
        submenu = tk.Menu(self.popup_menu)  # Colours
        self.popup_menu.add_cascade(label="Colour", underline=0, menu=submenu)
        submenu.add_command(label='Black', command=self.Black)
        submenu.add_command(label='Red', command=self.Red)
        submenu.add_command(label='Orange', command=self.Orange)
        submenu.add_command(label='Yellow', command=self.Yellow)
        submenu.add_command(label='Green', command=self.Green)
        submenu.add_command(label='Blue', command=self.Blue)
        submenu.add_command(label='Indigo', command=self.Indigo)
        submenu.add_command(label='Violet', command=self.Violet)

    def setstylePopupCommands(self):
        submenu = tk.Menu(self.popup_menu)  # Style
        self.popup_menu.add_cascade(label="Style", underline=0, menu=submenu)
        submenu.add_command(label='Plain', command=self.Plain)
        submenu.add_command(label='Bold', command=self.Bold)
        submenu.add_command(label='Italic', command=self.Italic)



    def setPopupCommands(self):
        #Override
        self.popup_menu.add_command(label='Sort node', command=self.sortNode)
        self.popup_menu.add_command(label='Set destination', command=self.setDestination)
        self.popup_menu.add_command(label='Hyperlink...', command=self.hyperlink)

    def getColour(self, item):
        tags=self.item(item)['tags']
        if 'black' in tags: return 'black'
        if 'red' in tags: return 'red'
        if 'orange' in tags: return 'orange'
        if 'yellow' in tags: return 'yellow'
        if 'green' in tags: return 'green'
        if 'blue' in tags: return 'blue'
        if 'indigo' in tags: return 'indigo'
        if 'violet' in tags: return 'violet'
        return None

    def getStyle(self,item):
        tags=self.item(item)['tags']
        if 'plain' in tags or 'hovered' in tags: return 'plain'
        if 'italic' in tags or 'hovered-italic' in tags: return 'italic'
        if 'bold' in tags or 'hovered-bold' in tags: return 'bold'
        if 'bold-italic' in tags or 'hovered-bold-italic' in tags: return 'bold-italic'
        return None

    def unsethoverItem(self,s):
        if s==None or not self.exists(s): return
        list = []
        style = self.getStyle(s)
        if style:
            if style=='bold': list.append('bold')
            if style=='bold-italic': list.append('bold-italic')
            if style=='italic': list.append('italic')
        colour=self.getColour(s)
        if colour: list.append(colour)
        self.item(s, tags=list)

    def sethoverItem(self, s):
        if s==None or not self.exists(s): return
        list = []
        style = self.getStyle(s)
        if style:
            if style=='plain': list.append('hovered')
            if style=='bold': list.append('hovered-bold')
            if style=='bold-italic': list.append('hovered-bold-italic')
            if style=='italic': list.append('hovered-italic')
        else:
            list.append('hovered')
        colour=self.getColour(s)
        if colour: list.append(colour)
        self.item(s, tags=list)

    def setcolourItem(self,s, colour):
        list = []
        style = self.getStyle(s)
        if style: list.append(style)
        list.append(colour)
        self.display.tree.item(s, tags=list)
        if self.display.chronotree.exists(s):
            self.display.chronotree.item(s, tags=list)

    def setstyleItem(self,s,str):
        list=[]
        colour=self.getColour(s)
        if colour: list.append(colour)
        list.append(str)
        self.display.tree.item(s,tags=list)
        if self.display.chronotree.exists(s):
            self.display.chronotree.item(s,tags=list)

    def setColour(self, colour):
        selectedList=[]
        for s in self.selection():
            oldTags=self.item(s)['tags']
            self.setcolourItem(s, colour)
            tags=self.item(s)['tags']
            options={'id':s,'tags': tags, 'old_tags': oldTags}
            selectedList.append(options)
        options={'code':"TOC_tagChanged", 'selectedList': selectedList}
        self.display.adddocHistory(options)
        self.display.readTree()

    def setStyle(self,str):
        selectedList=[]
        for s in self.selection():
            oldTags=self.item(s)['tags']
            self.setstyleItem(s,str)
            tags = self.item(s)['tags']
            options = {'id': s, 'tags': tags, 'old_tags': oldTags}
            selectedList.append(options)
        options={'code':"TOC_tagChanged", 'selectedList': selectedList}
        self.display.adddocHistory(options)
        self.display.readTree()


    def Black(self):
        self.setColour('black')
    def Red(self):
        self.setColour('red')
    def Orange(self):
        self.setColour('orange')
    def Yellow(self):
        self.setColour('yellow')
    def Green(self):
        self.setColour('green')
    def Blue(self):
        self.setColour('blue')
    def Indigo(self):
        self.setColour('indigo')
    def Violet(self):
        self.setColour('violet')
    def Plain(self):
        self.setStyle('plain')
    def Bold(self):
        self.setStyle('bold')
    def Italic(self):
        self.setStyle('italic')

    def selectAll(self,event):
        def search_tree(node, lvl):
            for child_node in self.get_children(node):
                self.selection_add(self.get_children(node))
                if self.get_children(child_node):
                    search_tree(child_node, lvl + 1)
        search_tree({}, 1)

    def setEditable(self):
        #override
        pass

    def expandTree(self):
        def search_tree(node, lvl):
            for child_node in self.get_children(node):
                self.item(self.parent(child_node), open=True)
                if self.get_children(child_node):
                    search_tree(child_node, lvl + 1)

        search_tree({}, 1)

    def collapseTree(self):
        def search_tree(node, lvl):
            for child_node in self.get_children(node):
                self.item(self.parent(child_node), open=False)
                if self.get_children(child_node):
                    search_tree(child_node, lvl + 1)
        search_tree({}, 1)

    def sortNode(self):
        print('sortnode')

    def setDestination(self):
        self.display.setDestination()

    def hyperlink(self):
        #get the right page range and pass to hyperlink dialog
        rangeStr=[]
        for s in self.selection():
            startPg=self.item(s)['values'][1]
            sibling=self.next(s)
            if sibling:
                endPg=self.display.doc[self.item(sibling)['values'][2]-2].get_label()
            else:
                endPg=self.display.doc[self.display.doc.page_count-1].get_label()
            rangeStr.append(str(startPg) + "-" + str(endPg))
        result=','.join(rangeStr)
        print (result)
        dlg=hyperlinkDialog(self.display.displayWindow,self.display, result)

    def sort(self, options=None):

        oldToc=self.display.doc.get_toc(simple=False)

        if options['column'] == '#0':
            self.display.updatestatusBar('Sorting tree A-Z...')
        elif options['column'] == 'Date':
            self.display.updatestatusBar('Sorting tree by Date...')
        elif options['column'] == 'Page Label':
            self.display.updatestatusBar('Sorting tree by Page Label...')
        elif options['column'] == 'Page':
            self.display.updatestatusBar('Sorting tree by Page...')

        settings = self.display.loadOptions()

        reverse = options['reverse']
        column = options['column']

        gluedNodes = self.getallGluedNodes()

        def AtoZ(e):
            if e[2]:
                return e[0], e[2]
            else:
                return e[0], datetime.datetime(1066, 10, 10)

        def byDt(e):
            if e[2]:
                return e[2], e[0]
            else:
                return datetime.datetime(1066, 10, 10), e[0]  # a very early date

        def byPageLabel(e):
            return str(e[3]) #gives odd results

        def byPage(e):
            return e[4]

        def search_tree(node, lvl, reverse, column):
            treeview_sort_column(self, node, reverse, column)
            for child_node in self.get_children(node):
                if self.get_children(child_node):
                    search_tree(child_node, lvl + 1, reverse, column)

        def treeview_sort_column(tree, node, reverse, column):
            l = [(tree.item(k)["text"], k, getdatefromNode(tree, k, settings), tree.item(k)['values'][1],
                  tree.item(k)['values'][2]) for k in tree.get_children(node)]  # Display column #0 cannot be set
            if column == '#0':
                l.sort(key=AtoZ, reverse=reverse)
            elif column == 'Date':
                l.sort(key=byDt, reverse=reverse)
            elif column == 'Page Label':
                l.sort(key=byPage, reverse=reverse) #deliberately use byPage
            elif column == 'Page':
                l.sort(key=byPage, reverse=reverse)

            for index, (val, k, dt, pglbl, pg) in enumerate(l):
                tree.move(k, node, index)

        search_tree("", 1, reverse, column)

        options['reverse'] = not options['reverse']
        self.heading(column, command=lambda: self.sort(options))  # switch reverse

        self.glueNodes(gluedNodes)

        self.display.readTree()

        newToc=self.display.doc.get_toc(simple=False)

        self.display.adddocHistory({'code':"TOC_sorted", "old_toc":oldToc, "new_toc":newToc})

        if options['column'] == '#0':
            self.display.updatestatusBar('Finished sorting tree A-Z...')
        elif options['column'] == 'Date':
            self.display.updatestatusBar('Finished sorting tree by Date...')
        elif options['column'] == 'Page Label':
            self.display.updatestatusBar('Finished sorting tree by Page Label...')
        elif options['column'] == 'Page':
            self.display.updatestatusBar('Finished sorting tree by Page...')

    def headingEvents(self):
        #to be overridden
        optionsA = {'reverse': False, 'column': '#0'}
        self.heading('#0', command=lambda: self.sort(optionsA))
        optionsB = {'reverse': False, 'column': 'Date'}
        self.heading('Date', command=lambda: self.sort(optionsB))
        optionsC = {'reverse': False, 'column': 'Page Label'}
        self.heading('Page Label', command=lambda: self.sort(optionsC))
        optionsD = {'reverse': False, 'column': 'Page'}
        self.heading('Page', command=lambda: self.sort(optionsD))

    def bindings(self):
        # Events for moving parts of tree
        self.bind("<ButtonPress-1>", self.bDown)
        self.bind("<ButtonPress-2>", self.bDown)
        self.bind("<ButtonRelease-1>", self.bUp, add='+')
        self.bind("<B1-Motion>", self.bMove, add='+')
        self.bind("<Motion>",self.MouseMove)
        self.bind("<Leave>",self.MouseLeave)
        self.bind("<ButtonRelease-1>", self.bRelease, add='+')
        self.bind("<Shift-ButtonPress-1>", self.bDown_Shift, add='+')
        self.bind("<Shift-ButtonRelease-1>", self.bUp_Shift, add='+')
        self.bind("<Double-Button-1>", self.onDoubleClick, add='+')
#        self.bind("<Button-1>", self.onClick, add='+')
        self.bind("<<TreeviewSelect>>", self.rowSelected, add='+')
        self.bind("<Button-2>", self.brightClick, add='+')
        self.bind('<BackSpace>', self.bDelete)
        self.bind('<Delete>', self.bDelete)
        if 'win32' in sys.platform:  # windows
            self.bind("<Control-b>", self.add_outline_item)
        elif 'darwin' in sys.platform: #mac os
            self.bind("<Command-b>", self.add_outline_item)
        else:
            raise RuntimeError("Unsupported operating system")

    def rowSelected(self,event):
        s=self.selection()
        if len(s)>0:
            pg = self.item(s[0])['values'][2] - 1
            self.see(s[0])
            self.display.setPage(pg)
            self.display.addpageHistory(pg)

    def MouseMove(self,event):
        tv = event.widget
        item = tv.identify_row(event.y)
        if not item==self.oldHoveredItem:
            self.unsethoverItem(self.oldHoveredItem)
        self.oldHoveredItem=item
        self.sethoverItem(item)

    def MouseLeave(self,event):
        self.unsethoverItem(self.oldHoveredItem)

    def build(self):
        #to be overridden
        colNames = ["Date", "Page Label", "Page"]
        self.config(columns=colNames)

        # columns
        self.column("#0", width=200, minwidth=100, stretch=tk.YES)
        self.column("Date", width=100, minwidth=50, stretch=tk.NO)
        self.column("Page Label", width=70, minwidth=50, stretch=tk.NO)
        self.column("Page", width=70, minwidth=50, stretch=tk.NO)

        self.heading("#0", text="Text", anchor=tk.W)
        self.heading("Date", text="Date", anchor=tk.W)
        self.heading("Page Label", text="Page Label", anchor=tk.E)
        self.heading("Page", text="Page", anchor=tk.E)

        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def emptyTree(self):
        self.delete(*self.get_children())

    def fillTree(self, chronotree=None):
        if not self.display.doc: return
        self.emptyTree()
        if chronotree: chronotree.emptyTree()
        TOC = self.display.doc.get_toc(simple=False)
        ids = [None] * 100
        ids[0]=''
        c=0
        dict, arr=getpgLabelMapping(self.display.doc)
        for t in TOC:
            c+=1
            pg = int(t[2])
            pgLbl=arr[pg-1]
            txt, dtPt, dt, dy=getsplit(t[1])
#            print (txt, dtPt, dt, dy)

#            pgLbl = self.display.doc[pg - 1].get_label()
#            dtPt = gettextpartDate(t[1])
#            txt = gettextfromText(t[1])
#            dt = getdatefromText(', ' + dtPt)
#            dy = getdayofWeek(dt)
            new_lvl = t[0]
            dict=t[-1]
            id = ids[new_lvl - 1]
            cur_id = self.insert(id, 'end', text=txt, values=(dtPt, pgLbl, pg))
            colorName=None
            bold=False
            italic=False
            if 'color' in dict:
                ctuple=converttoRGB(dict['color'])
                colorName=get_colour_name(ctuple)
                self.setcolourItem(cur_id,colorName)
                print(colorName)
            if 'bold' in dict:
                if dict['bold']:
                    bold=True
                    self.setstyleItem(cur_id,'bold')
            if 'italic' in dict:
                if dict['italic']:
                    italic=True
                    self.setstyleItem(cur_id,'italic')
            if not dtPt == "" and chronotree:
                chronotree.insert('', 'end', text=dtPt, iid=cur_id, values=(dy, txt, pgLbl, pg))
                if colorName: chronotree.setcolourItem(cur_id,colorName)
                if bold: chronotree.setstyleItem(cur_id,'bold')
                if italic: chronotree.setstyleItem(cur_id,'italic')
            ids[new_lvl] = cur_id
        #chronotree.sort()
        x=threading.Thread(target=self.sortChrono)
        x.start()
        print(c)

    def sortChrono(self):
        self.display.tab_parent.tab(1,state='disabled')
        self.display.chronotree.sort()
        self.display.tab_parent.tab(1,state='normal')


    def brightClick(self,event):
        rowid = self.identify_row(event.y)
        if not rowid: return
        self.selection_set(rowid)
        self.update()
        #TODO: show pop up
        try:
            self.popup_menu.tk_popup(event.x_root,event.y_root,0)
        except:
            self.popup_menu.grab_release()


    def selectSame(self, id):
        if self.display.chronotree.exists(id):
            self.display.chronotree.selection_set(id)
            self.display.chronotree.see(id)



    #if editable
    def editableColumn(self,column):
        col=int(column.replace('#',''))
        if col in self.editable:
            return True
        else:
            return False

    # edit label
    def onDoubleClick(self,event):
        ''' Executed, when a row is double-clicked. Opens
        read-only EntryPopup above the item's column, so it is possible
        to select text '''
        # close previous popups
        # self.destroyPopups()

        # what row and column was clicked on
        rowid = self.identify_row(event.y)
        if not rowid: return
        column = self.identify_column(event.x)
        #    column='#0'
        if self.editableColumn(column):
            self.editbookmark(rowid, column)
#            self.display.displayWindow.update()

    def editbookmark(self,id, column):

        # get column position info
        x, y, width, height = self.bbox(id, column)

        # y-axis offset
        # pady = height // 2
        pady = 7
        shift = 0
        col = int(column.replace('#', ''))

        # place Entry popup properly
        if col == 0:
            text = self.item(id, 'text')
            shift = 8
        else:
            text = self.item(id, 'values')[col - 1]
        entryPopup = EntryPopupBookMark(self, self.display.chronotree, id, text, col, self.display)
        entryPopup.place(x=x + shift, y=y + pady, anchor=tk.W, width=width - shift)
        return entryPopup

    # drag and drop functions
    def bDown_Shift(self,event):
        return
        tv = event.widget
        select = [tv.index(s) for s in tv.selection()]
        select.append(tv.index(tv.identify_row(event.y)))
        select.sort()
        parent = tv.parent(tv.identify_row(event.y))
        for i in range(select[0], select[-1] + 1, 1):
            tv.selection_add(tv.get_children(parent)[i])

    def add_outline_item(self,event):
        if not self.display.doc: return
        if self.display.doc.page_count==0: return
        print('adding bookmark')
        tv = self
        x = tv.selection()
        index=0
        locus=index+1
        pg = self.display.cur_page
        pgLbl = self.display.doc[pg].get_label()
        insertionPoint=''
        if len(tv.selection()) > 0:  # if there is selection
            sItem = x[0]  # select the first selection
            parent = tv.parent(sItem)
            no_children = len(tv.get_children(parent))
            index = tv.index(sItem)
            insertionPoint=tv.parent(sItem)
            if index + 1 >= no_children:
                locus='end'

        new_item = tv.insert(insertionPoint, locus, text="New Bookmark", values=("", pgLbl, pg + 1))
        tv.selection_set(new_item)
        self.display.readTree()
        entry = self.editbookmark(new_item, '#0')
        entry.select_all()
        options={'code':'TOC_addedItem', 'id':new_item, 'parentID':insertionPoint, 'locus':locus, 'text':"New Bookmark", 'values': ("",pgLbl, pg+1)}
        self.display.adddocHistory(options)


    def bshiftDown(self,event):
        try:
            self.popup_menu.tk_popup(event.x_root,event.y_root,0)
        except:
            self.popup_menu.grab_release()

    def bDown(self,event):
        self.gluedNodes=self.getallGluedNodes()
        tv = event.widget
        if tv.identify_row(event.y) not in tv.selection():
            tv.selection_set(tv.identify_row(event.y))

    def bUp(self,event):
        tv = event.widget
        if tv.identify_row(event.y) in tv.selection():
            tv.selection_set(tv.identify_row(event.y))

    def bUp_Shift(self,event):
        pass

    def bRelease(self,event):
        print('release')
        if self.moving:
            if not self.nodetoMove==None and not self.nodetoGoto==None and not self.nodetoGotoIndex==None:
                if self.exists(self.nodetoMove) and self.exists(self.nodetoGoto):
                    fr={'parent':self.parent(self.nodetoMove),'index':self.index(self.nodetoMove)}
                    self.move(self.nodetoMove, self.nodetoGoto, self.nodetoGotoIndex)
                    to={'parent':self.nodetoGoto, 'index':self.nodetoGotoIndex}
                    self.glueNodes(self.gluedNodes)
                    self.display.readTree()
                    print('release')
                    options={'code':'TOC_moveditem','id':self.nodetoMove, 'fr':fr, 'to':to}
                    self.display.adddocHistory(options)
            self.item(self.oldMovetoItem['id'], text=self.currentText)

        self.moving=False
        self.oldMovetoItem={'id':None,'text':''}

    def bMove(self,event):
        self.moving=True
        char=''
        tv = event.widget
        movetoItem = tv.identify_row(event.y) #where we are hovering
        movetoIndex = tv.index(movetoItem)
        print(movetoIndex)
        boxX = tv.bbox(movetoItem, '#0')

        if not movetoItem==self.oldMovetoItem['id']: #so we have new item hovered
            if self.oldMovetoItem['id']:
                tv.item(self.oldMovetoItem['id'],text=self.currentText)
                pass
            self.currentText=self.item(movetoItem)['text']

        print(self.currentText)
        print(event.y)

        LEFT = 0
        RIGHT = 1
        MOVE = RIGHT

        if boxX != "":
            if event.x < boxX[0] + 13 + 20:
                MOVE = LEFT  # directly under moveItem
            else:
                MOVE = RIGHT  # make first chld of movetoItem

        for s in tv.selection():
            tv.item(s, open=False)
            if MOVE == LEFT:
                parent = tv.parent(movetoItem)
                if not s==movetoItem: self.item(movetoItem, open=False)
                #if we do not share a common parent, increase by 1
                if not tv.parent(s)==parent:
                    movetoIndex+=1
                if tv.parent(s)==parent and tv.index(s)>tv.index(movetoItem):
                    movetoIndex+=1
                char="↓"
            if MOVE == RIGHT:
                parent = movetoItem
                if not s==movetoItem: self.item(parent, open=True)
                movetoIndex = 0
                char = "→"
            if event.y<15: char="↑" #i.e. above top row
            print(char)
            if not movetoItem==s:
                tv.item(movetoItem, text=char+self.currentText)
                self.nodetoMove=s
                self.nodetoGoto=parent
                self.nodetoGotoIndex=movetoIndex

            self.oldMovetoItem['id'] = movetoItem
            self.oldMovetoItem['text'] = self.item(movetoItem)['text']
            return

    def bDelete(self,event):
        tv = self
        new_item=None
        for s in tv.selection():
            try:
                new_item=tv.next(s)
                if not new_item:
                    new_item=tv.prev(s)
                parentID=self.parent(s)
                locus=self.index(s)
                txt=self.item(s)['text']
                values=self.item(s)['values']
                self.delete(s)
                options = {'code': 'TOC_deletedItem', 'id': s, 'parentID': parentID, 'locus': locus,
                           'text': txt, 'values': values}
                self.display.adddocHistory(options)
            except:
                pass
        #set new selected item to next item after last
        if new_item:
            tv.selection_set(new_item)
            tv.see(new_item) #so we can see it
            self.cur_page=tv.item(new_item)['values'][2]-1
            self.display.setPage()
        self.display.readTree()

    #sorting functions
    def getallGluedNodes(self):
        # returns list of nodes which are glued to their first child (i.e point to same page)
        nodes = []

        def search_tree(node, lvl):
            for child_node in self.get_children(node):
                if self.get_children(child_node):
                    x = self.get_children(child_node)[0]
                    if self.item(child_node)['values'][2] == self.item(self.get_children(child_node)[0])['values'][2]:
                        nodes.append(child_node)
                    search_tree(child_node, lvl + 1)

        search_tree("", 1)
        return nodes

    def glueNodes(self,nodes):
        # glues nodes
        for node in nodes:
            self.set(node, 2, self.item(self.get_children(node)[0])['values'][2])
            self.set(node, 1, self.display.doc[self.item(node)['values'][2] - 1].get_label())

class treebookMarks(treeClone):
    def setEditable(self):
        self.editable=(0,1,2,3)

    def bDelete(self,event):
        print('bookmark delete')
        self.selectedDeleted=[]
        def deleteallchrono(s):
            self.count=0
            def search_tree(node): #searches the bookmark tree
                for child_node in self.get_children(node):
                    self.count += 1
                    parentID = self.parent(child_node)
                    locus = self.index(child_node)
                    txt = self.item(child_node)['text']
                    values = self.item(child_node)['values']
                    tags= self.item(child_node)['tags']
                    options = {'id': child_node, 'parentID': parentID, 'locus': locus,
                               'text': txt, 'values': values, 'tags': tags}
                    self.deleteList.append(options)
                    if self.display.chronotree.exists(child_node):
                        self.display.chronotree.delete(child_node)
                    if self.get_children(child_node):
                        search_tree(child_node)
            search_tree(s)
            self.count += 1
            if self.display.chronotree.exists(s):
                self.display.chronotree.delete(s)
            return self.count #returns number of deletions

        tv = self
        new_item=None
        count=0
        for s in tv.selection():
            self.deleteList = []  # for storing all the child nodes that get deleted
            if self.exists(s):
                parentID=self.parent(s)
                locus=self.index(s)
                txt=self.item(s)['text']
                values=self.item(s)['values']
                tags = self.item(s)['tags']
                new_item=tv.next(s)
                if not new_item:
                    new_item=tv.prev(s)
                count+=deleteallchrono(s)
                options = {'id': s, 'parentID': parentID, 'locus': locus,
                           'text': txt, 'values': values, 'deleteList':self.deleteList, 'tags':tags}
                self.selectedDeleted.append(options)
                self.delete(s)
            else:
                #print(s)
                pass
        options={'code': "TOC_deletedItem", 'selectedList': self.selectedDeleted}
        self.display.adddocHistory(options)
        #set new selected item to next item after last
        self.display.updatestatusBar(str(count) + ' items deleted.')
        if new_item:
            tv.selection_set(new_item)
            tv.see(new_item) #so we can see it
            self.cur_page=tv.item(new_item)['values'][2]-1
            self.display.setPage()
        self.display.readTree()

class treeChrono(treeClone):

    def setPopupCommands(self):
        self.popup_menu.add_command(label='Set destination', command=self.setDestination)


    def bDelete(self,event):
        print('chrono delete')
        self.selectedDeleted=[]
        def countdeleted(s):
            self.count=0
            def search_tree(s):
                for child_node in self.display.tree.get_children(s):
                    self.count+=1
                    parentID = self.display.tree.parent(child_node)
                    locus = self.display.tree.index(child_node)
                    txt = self.display.tree.item(child_node)['text']
                    values = self.display.tree.item(child_node)['values']
                    tags= self.item(child_node)['tags']
                    options = {'id': child_node, 'parentID': parentID, 'locus': locus,
                               'text': txt, 'values': values, 'tags': tags}
                    self.deleteList.append(options)
                    if self.display.tree.get_children(child_node):
                        search_tree(child_node)
            search_tree(s)
            return self.count+1
        tv = self
        new_item=None
        count=0
        for s in tv.selection():
            self.deleteList = []  # for storing all the child nodes that get deleted
            if self.exists(s):
                parentID=self.display.tree.parent(s)
                locus=self.display.tree.index(s)
                txt=self.display.tree.item(s)['text']
                values=self.display.tree.item(s)['values']
                tags = self.item(s)['tags']
                new_item=tv.next(s)
                if not new_item:
                    new_item=tv.prev(s)
                count+=countdeleted(s)
                options = {'id': s, 'parentID': parentID, 'locus': locus,
                           'text': txt, 'values': values, 'deleteList':self.deleteList, 'tags':tags}
                self.selectedDeleted.append(options)
                self.delete(s)
                self.display.tree.delete(s)
            else:
                print(s)
        #set new selected item to next item after last
        options={'code': "TOC_deletedItem", 'selectedList': self.selectedDeleted}
        self.display.adddocHistory(options)
        self.display.updatestatusBar(str(count) + ' items deleted')
        if new_item:
            tv.selection_set(new_item)
            tv.see(new_item) #so we can see it
            self.cur_page=tv.item(new_item)['values'][3]-1
            self.display.setPage()
        self.display.readTree()

    def selectSame(self, id):
        if self.display.tree.exists(id):
            self.display.tree.selection_set(id)
            self.display.tree.see(id)


    def setEditable(self):
        self.editable=(0,2,3,4)

    def build(self):
        colNames = ["Day", "Text", "Page Label", "Page"]
        self.config(columns=colNames)

        # columns
        self.column("#0", width=100, minwidth=100, stretch=tk.YES)
        self.column("Day", width=50, minwidth=50, stretch=tk.NO)
        self.column("Text", width=400, minwidth=100, stretch=tk.NO)
        self.column("Page Label", width=70, minwidth=50, stretch=tk.NO)
        self.column("Page", width=70, minwidth=50, stretch=tk.NO)

        self.heading("#0", text="Date", anchor=tk.W)
        self.heading("Day", text="Day", anchor=tk.W)
        self.heading("Text", text="Text", anchor=tk.W)
        self.heading("Page Label", text="Page Label", anchor=tk.E)
        self.heading("Page", text="Page", anchor=tk.E)

        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def sort(self,options=None):
        settings = self.display.loadOptions()

        def byDt(e):
            if e[1]:
                return e[1]
            else:
                return datetime.datetime(1066, 10, 10)  # a very early date

        def search_tree(node, lvl):
            treeview_sort_column(self, node)
            for child_node in self.get_children(node):
                if self.get_children(child_node):
                    search_tree(child_node, lvl + 1)

        def treeview_sort_column(tree, node):
            l = [(k, getdatefromText(", " + tree.item(k)["text"], settings)) for k in
                 tree.get_children(node)]  # Display column #0 cannot be set
            l.sort(key=byDt)

            for index, (k, dt) in enumerate(l):
                tree.move(k, node, index)

        search_tree("", 1)

    def fillTree(self):
        pass

    def headingEvents(self):
        pass

    def bindings(self):
        self.bind("<Motion>",self.MouseMove)
        self.bind("<Leave>",self.MouseLeave)
        self.bind("<Double-Button-1>", self.onDoubleClick, add='+')
        self.bind("<<TreeviewSelect>>", self.rowSelected)
        self.bind("<ButtonPress-2>", self.bDown)
        self.bind("<Button-2>", self.brightClick, add='+')
        self.bind('<BackSpace>', self.bDelete)
        self.bind('<Delete>', self.bDelete)


    def rowSelected(self,event):
        s=self.selection()
        if len(s)>0:
            pg = self.item(s[0])['values'][3] - 1
            self.see(s[0])
            self.display.addpageHistory(pg)
            self.display.setPage(pg)

    # edit label
    def editbookmark(self,id, column):

        # get column position info
        x, y, width, height = self.bbox(id, column)

        # y-axis offset
        # pady = height // 2
        pady = 7
        shift = 0
        col = int(column.replace('#', ''))

        # place Entry popup properly
        if col == 0:
            text = self.item(id, 'text')
            shift = 8
        else:
            text = self.item(id, 'values')[col - 1]
        entryPopup = EntryPopupChrono(self, self.display.tree, id, text, col, self.display)
        entryPopup.place(x=x + shift, y=y + pady, anchor=tk.W, width=width - shift)
        return entryPopup

class treeMerge(treeClone):

    def setPopupCommands(self):
        pass

    def deleteFull(self):
        new_item=None
        sel=[]
        for s in self.selection():
            try:
                new_item=self.next(s)
                if not new_item:
                    new_item=self.prev(s)
                self.delete(s)
                sel.append(s)
            except:
                pass
        #set new selected item to next item after last
        if new_item:
            self.selection_set(new_item)
            self.see(new_item) #so we can see it
        return sel


    def bDelete(self,event):
        tv = event.widget
        self.deleteFull()

    def setEditable(self):
        self.editable=(1,4)

    def fillTree(self):
        pass

    def sort(self):
        pass

    def build(self):
        colNames = ["Page Range", "Size", "No pages", "Bookmark for File"]
        self.config(columns=colNames)

        # columns
        self.column("#0", width=200, minwidth=100, stretch=tk.YES)
        self.column("Page Range", width=100, minwidth=50, stretch=tk.NO)
        self.column("Size", width=100, minwidth=100, stretch=tk.NO)
        self.column("No pages", width=70, minwidth=50, stretch=tk.NO)
        self.column("Bookmark for File", width=200, minwidth=50, stretch=tk.YES)

        self.heading("#0", text="File", anchor=tk.W)
        self.heading("Page Range", text="Page Range", anchor=tk.W)
        self.heading("Size", text="Size", anchor=tk.W)
        self.heading("No pages", text="No pages", anchor=tk.W)
        self.heading("Bookmark for File", text="Bookmark for File", anchor=tk.W)

        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pass

    def bindings(self):

        self.bind("<ButtonPress-1>", self.bDown)
        self.bind("<ButtonPress-2>", self.bDown)
        self.bind("<ButtonRelease-1>", self.bUp, add='+')
        self.bind("<B1-Motion>", self.bMove, add='+')
        self.bind("<Shift-ButtonPress-1>", self.bDown_Shift, add='+')
        self.bind("<Shift-ButtonRelease-1>", self.bUp_Shift, add='+')
        self.bind("<Double-Button-1>", self.onDoubleClick, add='+')
        self.bind("<Button-1>", self.onClick, add='+')
        self.bind("<Button-2>", self.brightClick, add='+')
        self.bind('<BackSpace>', self.bDelete)
        self.bind('<Delete>', self.bDelete)

    # display page of bookmark
    def onClick(self,event):
        rowid = self.identify_row(event.y)
        if not rowid: return
        pg = self.item(rowid)['values'][2]-1



    def bMove(self,event):
        tv = event.widget
        movetoItem = tv.identify_row(event.y)
        movetoIndex = tv.index(movetoItem)
        boxX = tv.bbox(movetoItem, '#0')

        LEFT = 0
        RIGHT = 1
        MOVE = LEFT

        for s in tv.selection():
            try:
                if MOVE == LEFT:
                    parent = tv.parent(movetoItem)
                if MOVE == RIGHT:
                    parent = movetoItem
                    self.item(parent, open=True)
                    movetoIndex = 0
                tv.move(s, parent, movetoIndex)
            except:
                return

    def headingEvents(self):
        pass

    def editbookmark(self,id, column):
        # get column position info
        x, y, width, height = self.bbox(id, column)

        # y-axis offset
        # pady = height // 2
        pady = 7
        shift = 0
        col = int(column.replace('#', ''))

        # place Entry popup properly
        if col == 0:
            text = self.item(id, 'text')
            shift = 8
        else:
            text = self.item(id, 'values')[col - 1]
        entryPopup = EntryPopupMerge(self, None, id, text, col, self.display)
        entryPopup.place(x=x + shift, y=y + pady, anchor=tk.W, width=width - shift)
        return entryPopup
