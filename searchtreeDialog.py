import re
import tkinter as tk
import tkinter.ttk as ttk


class searchtreeDialog():
    
    def __init__(self, parent, tree, mirrortree, display):
        self.parent=parent
        self.tree=tree #tree to search
        self.mirrortree=mirrortree #mirrortree with same iid
        self.display=display

        self.bookmarksofInterest = []  # for storing bookmarks of interest
        self.indexbookMark = 0  # index of particular bookmark of interest

        self.displayDialog()

    def __del__(self):
        pass

    def displayDialog(self):
        
        def search(search):
            if search=="": return
            options = {}
            if 'selected' in cbignoreCase.state():
                options['ignoreCase'] = True
            else:
                options['ignoreCase'] = False
            if 'selected' in cbRegex.state():
                options['useRegex'] = True
            else:
                options['useRegex'] = False
            self.searchbookMarks(search, options)
    
        def replace(search, replace):
            # replace selected node
            if search=="": return
            options = {}
            options['selectedOnly'] = True
            if 'selected' in cbrLabel.state():
                options['replacementText']=replace
            if 'selected' in cbColour.state():
                options['colour']=textVarCol.get()
            if 'selected' in cbStyle.state():
                options['style']=textVarStyle.get()
            if 'selected' in cbignoreCase.state():
                options['ignoreCase'] = True
            else:
                options['ignoreCase'] = False
            if 'selected' in cbRegex.state():
                options['useRegex'] = True
            else:
                options['useRegex'] = False
            self.replaceselectedBookmarks(search, replace, options)
            self.incBkMk()
    
        def replaceAll(search, replace):
            # replaces all
            if search=="": return
            options = {}
            options['selectedOnly'] = False
            if 'selected' in cbrLabel.state():
                options['replacementText']=replace
            if 'selected' in cbColour.state():
                options['colour']=textVarCol.get()
            if 'selected' in cbStyle.state():
                options['style']=textVarStyle.get()
            if 'selected' in cbignoreCase.state():
                options['ignoreCase'] = True
            else:
                options['ignoreCase'] = False
            if 'selected' in cbRegex.state():
                options['useRegex'] = True
            else:
                options['useRegex'] = False
            self.replacebookMarks(search, replace, options)
    
        def onReturn(i):
            #if there are no bookmarks of interest, do first search
            #otherwise go to next bookmark
            if e1.get()=="": return
            if len(self.bookmarksofInterest)==0:
                search(e1.get())
            else:
                self.incBkMk()

        def onClosing():
            print('closing')
            self.display.updatestatusBar("")
            searchWindow.destroy()

        def onEscape(i):
            searchWindow.destroy()
    
        searchWindow = tk.Toplevel(self.parent)
        searchWindow.title('Search bookmarks')
        searchWindow.attributes('-topmost', True)
        searchWindow.resizable(True,False)

        Frame1=tk.LabelFrame(searchWindow, text='Search')
        Frame1.pack(fill=tk.X, padx=5, pady=5)

        Frame12=tk.Frame(Frame1)
        Frame12.pack(fill=tk.X)
        sLabel=tk.Label(Frame12, text="Text:")
        sLabel.pack(side=tk.LEFT)
        e1 = tk.Entry(Frame12)
        e1.pack(side=tk.RIGHT, fill=tk.X, expand=1, padx=5)

        Frame4 = tk.Frame(Frame1)
        Frame4.pack(fill=tk.X,padx=5, pady=5)

        cbignoreCase = ttk.Checkbutton(Frame4, text="Ignore case")
        cbignoreCase.state(['!alternate'])
        cbignoreCase.state(['selected'])
        cbignoreCase.pack(side=tk.LEFT, expand=1, fill=tk.X)

        cbRegex = ttk.Checkbutton(Frame4, text="Use regex")
        cbRegex.state(['!alternate'])
        cbRegex.pack(side=tk.RIGHT, expand=1, fill=tk.X)

        Frame2 = tk.LabelFrame(searchWindow, text='Replace')
        Frame2.pack(fill=tk.X,padx=5, pady=5)

        Frame22=tk.Frame(Frame2)
        Frame22.pack(fill=tk.X)

        cbrLabel = ttk.Checkbutton(Frame22, text="Text:")
        cbrLabel.state(['!alternate'])
        cbrLabel.state(['selected'])
        cbrLabel.pack(side=tk.LEFT)
        e2 = tk.Entry(Frame22)
        e2.pack(side=tk.RIGHT, fill=tk.X, expand=1, padx=5)

        Frame24=tk.Frame(Frame2)
        Frame24.pack(fill=tk.X)

        Frame25=tk.Frame(Frame24)
        Frame25.pack(fill=tk.X,padx=5, pady=5)
        cbColour = ttk.Checkbutton(Frame24, text="Colour")
        cbColour.state(['!alternate'])
        cbColour.pack(side=tk.LEFT, fill=tk.X,padx=5, pady=5)
        textVarCol=tk.StringVar()
        textVarCol.set('Black')
        colourChoices = ['Black', 'Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Indigo', 'Violet']
        colourOption = tk.OptionMenu(Frame24, textVarCol, *colourChoices)
        colourOption.pack(side=tk.LEFT,fill=tk.X, expand=1,pady=5)

        cbStyle = ttk.Checkbutton(Frame24, text="Style")
        cbStyle.state(['!alternate'])
        cbStyle.pack(side=tk.LEFT, padx=5, fill=tk.X,pady=5)
        textVarStyle=tk.StringVar()
        textVarStyle.set('Plain')
        styleChoices = ['Plain', 'Bold', 'Italic', 'Bold-Italic']
        styleOption = tk.OptionMenu(Frame24, textVarStyle, *styleChoices)
        styleOption.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)

        Frame3=tk.Frame(searchWindow)
        Frame3.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(Frame3, text='Search', command=lambda: search(e1.get())).pack(side=tk.LEFT, expand=1, fill=tk.X)
        tk.Button(Frame3, text='Replace', command=lambda: replace(e1.get(), e2.get())).pack(side=tk.LEFT, expand=1, fill=tk.X)
        tk.Button(Frame3, text='Replace All', command=lambda: replaceAll(e1.get(), e2.get())).pack(side=tk.LEFT, expand=1, fill=tk.X)

        Frame5 = tk.Frame(searchWindow)
        Frame5.pack(fill=tk.X,padx=5, pady=5)
        lButton=tk.Button(Frame5,text='<', command=lambda: self.decBkMk())
        lButton.pack(side=tk.LEFT, expand=1, fill=tk.X)
        rButton=tk.Button(Frame5,text='>', command=lambda: self.incBkMk())
        rButton.pack(side=tk.RIGHT, expand=1, fill=tk.X)

        searchWindow.bind('<Return>',lambda i : onReturn(i))
        searchWindow.bind('<Key-Escape>',lambda i : onEscape(i))
        searchWindow.protocol('WM_DELETE_WINDOW', onClosing)

        e1.focus_set()


    def getText(self, s):
        return '' #to be overridden

    def setText(self, item, txt):
        self.tree.item(item, text=txt)
        return #to be overridden

    def replaceselectedBookmarks(self, srch, replace, options=None):
        if not options: options = {'ignoreCase': True}
        self.tree.LabelEdit = True
        count=0 #to count number of replacements
        for s in self.tree.selection():
            if 'colour' in options:
                #colour
                self.tree.setcolourItem(s,options['colour'])
            if 'style' in options:
                #style
                self.tree.setstyleItem(s,options['style'])
            txt =self.getText(s)
            new_txt=txt
            if options['ignoreCase']:
                if options['useRegex']:
                    new_txt=re.sub(srch, replace, txt)
                else:
                    new_txt=txt.replace(srch, replace)
            else:
                if options['useRegex']:
                    new_txt=re.sub(srch, replace, txt, flags=re.I)
                else:
                    new_txt=txt.replace(srch, replace)
            if not new_txt==txt:
                count +=1
            if 'replacementText' in options:
                self.setText(s,new_txt)
        self.display.updatestatusBar(str(count) + " replacements made.")
        self.display.readTree()

    def replacebookMarks(self, srch, replace, options=None):
        global doc
        if not options: options = {'ignoreCase': True}
        self.tree.LabelEdit = True
        self.count=0

        def search_tree(node, lvl):
            for child_node in self.tree.get_children(node):
                txt = self.getText(child_node)
                new_txt=txt
                if options['ignoreCase']:
                    if options['useRegex']:
                        new_txt=re.sub(srch, replace, txt)
                    else:
                        new_txt=txt.replace(srch, replace)
                else:
                    if options['useRegex']:
                        new_txt=re.sub(srch, replace, txt, flags=re.I)
                    else:
                        new_txt=txt.replace(srch, replace)
                if not new_txt == txt:#i.e. a match
                    if 'colour' in options:
                        # colour
                        self.tree.setcolourItem(child_node, options['colour'])
                    if 'style' in options:
                        # style
                        self.tree.setstyleItem(child_node, options['style'])
                    self.count += 1
                if 'replacementText' in options:
                    self.setText(child_node, new_txt)
                if self.tree.get_children(child_node):
                    search_tree(child_node, lvl + 1)

        search_tree({}, 0)
        print (self.count)
        self.display.updatestatusBar(str(self.count) + " replacements made.")
        self.display.readTree()

    def searchbookMarks(self, srch, options=None):
        if not options: options = {'ignoreCase': True}
        self.collapseTree()

        self.bookmarksofInterest.clear()

        def search_tree(node, lvl):
            for child_node in self.tree.get_children(node):
                txt = self.getText(child_node)
                if options['ignoreCase']:
                    if options['useRegex']:
                        res = re.search(srch, txt, re.IGNORECASE)
                    else:
                        if txt.upper().find(srch.upper()) == -1:
                            res = False
                        else:
                            res = True
                else:
                    if options['useRegex']:
                        res = re.search(srch, txt)
                    else:
                        if txt.find(srch) == -1:
                            res = False
                        else:
                            res = True
                if res:
                    self.bookmarksofInterest.append(child_node)
                else:
                    self.tree.item(child_node)['open'] = False
                if self.tree.get_children(child_node):
                    search_tree(child_node, lvl + 1)

        search_tree({}, 0)
        if len(self.bookmarksofInterest) > 0:  # show the first one if found
            self.indexbookMark = 0
            self.showbookmark(self.bookmarksofInterest[0])
        else:
            self.display.updatestatusBar("None found.")

    def getPage(self,item):
        #to be overridden
        return self.tree.item(item)['values'][2]

    def showbookmark(self, item):
        self.display.updatestatusBar("Found " + str(self.indexbookMark + 1) + "/" + str(len(self.bookmarksofInterest)))
        self.tree.selection_set(item)
        self.tree.see(item)
        pg = self.getPage(item)
        self.display.addpageHistory(pg-1)
        self.display.setPage(pg - 1)

    def incBkMk(self):
        if not self.bookmarksofInterest: return
        self.indexbookMark += 1
        if self.indexbookMark > len(self.bookmarksofInterest) - 1:
            self.indexbookMark = 0
        if self.indexbookMark < len(self.bookmarksofInterest):
            self.showbookmark(self.bookmarksofInterest[self.indexbookMark])

    def decBkMk(self):
        if not self.bookmarksofInterest: return
        self.indexbookMark -= 1
        if self.indexbookMark < 0:
            self.indexbookMark = len(self.bookmarksofInterest) - 1
        if self.indexbookMark < len(self.bookmarksofInterest):
            self.showbookmark(self.bookmarksofInterest[self.indexbookMark])


    def collapseTree(self):

        def search_tree(node, lvl):
            for child_node in self.tree.get_children(node):
                self.tree.item(self.tree.parent(child_node), open=False)
                if self.tree.get_children(child_node):
                    search_tree(child_node, lvl + 1)

        search_tree({}, 1)

class searchtreeDialogBookmarks(searchtreeDialog):
    def getText(self, s):
        return self.tree.item(s)['text']
    def getPage(self, item):
        return self.tree.item(item)['values'][2]
    def setText(self, item, txt):
        self.tree.item(item, text=txt)
        if self.mirrortree.exists(item):
            self.mirrortree.set(item, 1, txt) #set the mirror

class searchtreeDialogChrono(searchtreeDialog):
    def getText(self, s):
        return self.tree.item(s)['values'][1]
    def getPage(self, item):
        return self.tree.item(item)['values'][3]
    def setText(self, item, txt):
        self.tree.set(item, 1, txt)
        if self.mirrortree.exists(item):
            self.mirrortree.item(item, text=txt)
