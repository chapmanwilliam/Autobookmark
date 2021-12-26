import tkinter as tk
from wwc_paginatepdf import paginate, remove_pagination

class paginateDialog(tk.Toplevel):

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

        def removepagination():
            if x.get()==2:
                #check page range
                if not self.display.doc.parse_page_string(e1.get()): return
            options=getOptions()
            remove_pagination(self.display.doc,options, self.display)
            self.display.displayPage()
            self.display.savepaginationOptions(options)


        def dopaginate():
            if x.get()==2:
                #check page range
                if not self.display.doc.parse_page_string(e1.get()): return
            options=getOptions()
            paginate(self.display.doc,options, self.display)
            self.display.displayPage()
            self.display.savepaginationOptions(options)


        def setOptions(options):
            if options['HPOS']=='L':
                v.set(1)
            elif options['HPOS']=='C':
                v.set(2)
            else:
                v.set(3)

            if options['VPOS']=='T':
                w.set(1)
            elif options['VPOS']=='M':
                w.set(2)
            else:
                w.set(3)

            m1.delete(0,tk.END)
            m1.insert(0,str(options['vMargin']))
            m2.delete(0,tk.END)
            m2.insert(0,str(options['hMargin']))

            boldVar.set(options['bBold'])
            italicVar.set(options['bItalic'])

            textVarFont.set(options['fontName'])

            textVarColour.set(options['Colour'])
            fontSizeVar.set(options['Size'])
            e1.delete(0,tk.END)
            if options['pgRange']: e1.insert(0,options['pgRange'])
            if options['All']:
                x.set(1)
            else:
                x.set(2)

        def getDefaults():
            options=self.display.getpaginationdefaultOptions()
            self.display.savepaginationOptions(options)
            return options


        def getOptions():
            HPOS=('L' if (v.get()==1) else
                  'C' if (v.get()==2) else
                  'R'
                  )
            VPOS=('T' if (w.get()==1) else
                  'M' if (w.get()==2) else
                  'B'
                  )
            vMargin=float(m1.get())
            hMargin=float(m2.get())
            bBold=boldVar.get()
            bItalic=italicVar.get()
            colour=textVarColour.get()
            fontName=textVarFont.get()
            size=fontSizeVar.get()
            pgRange=(e1.get() if (x.get()==2) else
                     None
                     )
            All=(True if (x.get()==1) else
                 False)

            options={
                'HPOS': HPOS,
                'VPOS': VPOS,
                'vMargin': vMargin,
                'hMargin': hMargin,
                'bBold': bBold,
                'bItalic': bItalic,
                'Colour': colour,
                'fontName': fontName,
                'Size': size,
                'pgRange':pgRange,
                'All': All
            }
            return options

        def defaults():
            setOptions(getDefaults())

        def showHChoice():
            pass

        def showVChoice():
            pass

        def showpgRangeChoice():
            if x.get()==1:
                e1.configure(state='disabled')
            else:
                e1.configure(state='normal')

        self.title('Pagination')
        self.attributes('-topmost', True)



        f0=tk.Frame(self)
        f0.pack(fill=tk.X, padx=5)
        v=tk.IntVar()
        tk.Radiobutton(f0,text='Left',variable=v,value=1, command=showHChoice).pack(side=tk.LEFT,padx=5,pady=5)
        tk.Radiobutton(f0,text='Centre',variable=v,value=2, command=showHChoice).pack(side=tk.LEFT,padx=5,pady=5)
        tk.Radiobutton(f0,text='Right',variable=v,value=3, command=showHChoice).pack(side=tk.LEFT,padx=5,pady=5)
        m1=tk.Entry(f0)
        m1.pack(side=tk.RIGHT, expand=1, fill=tk.X)
        tk.Label(f0, text='Margin (inches):').pack(side=tk.RIGHT, padx=5, pady=5)

        f1=tk.Label(self)
        w=tk.IntVar()
        f1.pack(fill=tk.X, padx=5)
        tk.Radiobutton(f1,text='Top',variable=w,value=1, command=showVChoice).pack(side=tk.LEFT,padx=5,pady=5)
        tk.Radiobutton(f1,text='Middle',variable=w,value=2, command=showVChoice).pack(side=tk.LEFT,padx=5,pady=5)
        tk.Radiobutton(f1,text='Bottom',variable=w,value=3, command=showVChoice).pack(side=tk.LEFT,padx=5,pady=5)
        m2=tk.Entry(f1)
        m2.pack(side=tk.RIGHT, expand=1, fill=tk.X)
        tk.Label(f1,text='Margin (inches):').pack(side=tk.RIGHT, padx=5, pady=5)

        f4=tk.Frame(self)
        f4.pack(fill=tk.X, padx=5)
        l1=tk.Label(f4,text='Font:')
        l1.pack(side=tk.LEFT,padx=5,pady=5)
        textVarFont=tk.StringVar()
        textVarFont.set('Helvetica')
        fontChoices = ['Courier', 'Helvetica', 'Times Roman']
        fontOption = tk.OptionMenu(f4, textVarFont, *fontChoices)
        fontOption.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)

        l2=tk.Label(f4,text='Size:')
        l2.pack(side=tk.LEFT,padx=5,pady=5)
        fontSizeVar=tk.IntVar()
        fontSize = tk.Spinbox(f4,from_=8, to=60, textvariable=fontSizeVar)
        fontSize.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)

        f5=tk.Frame(self)
        f5.pack(fill=tk.X,padx=5)
        boldVar=tk.IntVar()
        c1=tk.Checkbutton(f5,text='Bold',variable=boldVar)
        c1.pack(side=tk.LEFT)
        italicVar=tk.IntVar()
        c2=tk.Checkbutton(f5,text='Italic',variable=italicVar)
        c2.pack(side=tk.LEFT)

        l2=tk.Label(f5,text='Colour:')
        l2.pack(side=tk.LEFT,padx=5,pady=5)
        textVarColour=tk.StringVar()
        textVarColour.set('Black')
        colourChoices = ['Black', 'Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Indigo', 'Violet']
        colourOption = tk.OptionMenu(f5, textVarColour, *colourChoices)
        colourOption.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)


        f3=tk.LabelFrame(self, text='Page range')
        f3.pack(fill=tk.X, padx=5)
        x=tk.IntVar()
        tk.Radiobutton(f3,text='All',variable=x,value=1, command=showpgRangeChoice).pack(anchor=tk.W,padx=5,pady=5)
        tk.Radiobutton(f3,text='Page range:',variable=x,value=2, command=showpgRangeChoice).pack(side=tk.LEFT,padx=5,pady=5)


        e1=tk.Entry(f3)
        e1.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)




        if self.pgRange: #set pgRange if supplied
            e1.delete(0,tk.END)
            e1.insert(0,self.pgRange)


        f3=tk.Frame(self)
        f3.pack(fill=tk.X, padx=5, pady=5)

        okButton=tk.Button(f3,text='Paginate', command=dopaginate)
        okButton.pack(side=tk.RIGHT)

        removeButton=tk.Button(f3,text='Remove pagination', command=removepagination)
        removeButton.pack(side=tk.RIGHT)

        cancelButton=tk.Button(f3,text='Cancel', command=onClosing)
        cancelButton.pack(side=tk.RIGHT)

        defaultButton=tk.Button(f3,text='Set defaults', command=defaults)
        defaultButton.pack(side=tk.LEFT)


        options=self.display.getpaginationOptions()
        if not options: options=getDefaults()
        setOptions(options)

        self.bind('<Key-Escape>', lambda i: onEscape(i))
        self.protocol('WM_DELETE_WINDOW', onClosing)





