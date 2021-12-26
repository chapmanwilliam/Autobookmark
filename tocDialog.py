import tkinter as tk
from wwc_TOC import write_toc, delete_toc, isTOC

class tocDialog(tk.Toplevel):

    def __init__(self, parent, display):
        tk.Toplevel.__init__(self, parent)
        self.parent=parent
        self.display=display

        self.displayDialog()




    def displayDialog(self):

        def buttons():
            if isTOC(self.display.doc):
                okButton.config(text='Replace TOC')
                removeButton.config(state='normal')
            else:
                okButton.config(state='normal')
                removeButton.config(state='disabled')


        def onClosing():
            print('closing')
            self.display.updatestatusBar("")
            self.destroy()

        def onEscape(i):
            onClosing()

        def getOptions():
            options={"title":e1.get(), "maxDepth":intVardepth.get()}
            return options

        def setOptions(options):
            e1.delete(0, tk.END)
            e1.insert(0, options['title'])
            if options['maxDepth']<=self.display.doc.max_depth():
                intVardepth.set(options['maxDepth'])
            else:
                intVardepth.set(self.display.doc.max_depth())

        def getDefaults():
            options=self.display.gettocdefaultOptions()
            self.display.savetocOptions(options)
            return options


        def addTOC():
            self.display.updatestatusBar('Making TOC...')
            if write_toc(self.display.doc, getOptions(), self.display):
                onClosing()
                self.display.setPage(0)
                self.display.updatestatusBar('Finished TOC.')

        def removeTOC():
            options={}
            options['pgRange']=e1.get()
            self.display.updatestatusBar('Removing TOC...')
            if delete_toc(self.display.doc, options, self.display):
                onClosing()
                self.display.setPgDisplay()
                self.display.updatestatusBar('Finished removing TOC.')

        self.title('Table of Contents')
        self.attributes('-topmost', True)

        f1=tk.Frame(self)
        f1.pack(fill=tk.X, padx=5)

        l1=tk.Label(f1,text='Title:')
        l1.pack(side=tk.LEFT,padx=5,pady=5)
        e1=tk.Entry(f1)
        e1.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)


        f2=tk.Frame(self)
        f2.pack(fill=tk.X, padx=5)
        l1=tk.Label(f2,text='Depth:')
        l1.pack(side=tk.LEFT,padx=5,pady=5)
        intVardepth=tk.IntVar()
        depthChoices = [x for x in range(1,self.display.doc.max_depth()+1)]
        depthOption = tk.OptionMenu(f2, intVardepth, *depthChoices)
        depthOption.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)

        f3=tk.Frame(self)
        f3.pack(fill=tk.X, padx=5, pady=5)
        okButton=tk.Button(f3,text='Add TOC', command=addTOC)
        okButton.pack(side=tk.RIGHT)
        removeButton = tk.Button(f3, text='Remove TOC', command=removeTOC)
        removeButton.pack(side=tk.RIGHT)

        cancelButton=tk.Button(f3,text='Cancel', command=onClosing)
        cancelButton.pack(side=tk.RIGHT)

        options=self.display.gettocOptions()
        if not options: options=getDefaults()
        setOptions(options)
        buttons()


        self.bind('<Key-Escape>', lambda i: onEscape(i))
        self.protocol('WM_DELETE_WINDOW', onClosing)





