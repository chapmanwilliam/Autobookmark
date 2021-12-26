import tkinter as tk
from wwc_hyperlinkpagerefs import hyperlink, remove_links

class hyperlinkDialog(tk.Toplevel):

    def __init__(self, parent, display, pgRange=None):
        tk.Toplevel.__init__(self, parent)
        self.parent=parent
        self.display=display
        self.pgRange=pgRange

        self.displayDialog()




    def displayDialog(self):

        def onClosing():
            print('closing')
            self.display.updatestatusBar("")
            self.destroy()

        def onEscape(i):
            onClosing()

        def hyperLink():
            options={}
            options['pgRange']=e1.get()
            self.display.updatestatusBar('Hyperlinking...')
            if hyperlink(self.display.doc, self.display, options):
                onClosing()
                self.display.updatestatusBar('Finished hyperlinking.')

        def removeLinks():
            options={}
            options['pgRange']=e1.get()
            self.display.updatestatusBar('Removing links...')
            if remove_links(self.display.doc, self.display, options):
                onClosing()
                self.display.updatestatusBar('Finished removing links.')

        self.title('Hyperlink')
        self.attributes('-topmost', True)

        f1=tk.Frame(self)
        f1.pack(fill=tk.X, padx=5)

        l1=tk.Label(f1,text='Page range:')
        l1.pack(side=tk.LEFT,padx=5,pady=5)
        e1=tk.Entry(f1)
        e1.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)

        if self.pgRange: #set pgRange if supplied
            e1.delete(0,tk.END)
            e1.insert(0,self.pgRange)

        f2=tk.Frame(self)
        f2.pack(fill=tk.X, padx=5)
        l1=tk.Label(f2,text='Page ref style:')
        l1.pack(side=tk.LEFT,padx=5,pady=5)
        textVarpgRefs=tk.StringVar()
        textVarpgRefs.set('[]')
        styleChoices = ['[]', '{}', 'page', 'pg']
        styleOption = tk.OptionMenu(f2, textVarpgRefs, *styleChoices)
        styleOption.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)

        f3=tk.Frame(self)
        f3.pack(fill=tk.X, padx=5, pady=5)
        okButton=tk.Button(f3,text='Add links', command=hyperLink)
        okButton.pack(side=tk.RIGHT)
        removeButton = tk.Button(f3, text='Remove links', command=removeLinks)
        removeButton.pack(side=tk.RIGHT)

        cancelButton=tk.Button(f3,text='Cancel', command=onClosing)
        cancelButton.pack(side=tk.RIGHT)


        self.bind('<Key-Escape>', lambda i: onEscape(i))
        self.protocol('WM_DELETE_WINDOW', onClosing)





