import tkinter as tk

class rotateDialog(tk.Toplevel):

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

        def rotate():
            if v.get()==2:
                #check page range
                if not self.display.doc.parse_page_string(e1.get()): return
            self.display.updatestatusBar('Rotating...')
            if textVarDegrees.get()=="Counterclockwise 90 degrees":
                degrees=-90
            if textVarDegrees.get()=="Clockwise 90 degrees":
                degrees=90
            if textVarDegrees.get()=="180 degrees":
                degrees=180
            if v.get()==1:
                self.display.rotate(degrees)
            else:
                self.display.rotate(degrees, pgRange=e1.get())
            self.display.updatestatusBar('Finished rotating.')
            onClosing()

        def showChoice():
            if v.get()==1:
                e1.configure(state='disabled')
            else:
                e1.configure(state='normal')

        self.title('Rotation')
        self.attributes('-topmost', True)

        f2=tk.Frame(self)
        f2.pack(fill=tk.X, padx=5)
        l1=tk.Label(f2,text='Direction:')
        l1.pack(side=tk.LEFT,padx=5,pady=5)
        textVarDegrees=tk.StringVar()
        textVarDegrees.set('Counterclockwise 90 degrees')
        rotationChoices = ['Counterclockwise 90 degrees', 'Clockwise 90 degress', '180 degrees']
        rotationOption = tk.OptionMenu(f2, textVarDegrees, *rotationChoices)
        rotationOption.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)


        f0=tk.LabelFrame(self, text='Page range')
        f0.pack(fill=tk.X, padx=5)

        v=tk.IntVar()
        tk.Radiobutton(f0,text='All',variable=v,value=1, command=showChoice).pack(anchor=tk.W,padx=5,pady=5)
        tk.Radiobutton(f0,text='Page range:',variable=v,value=2, command=showChoice).pack(side=tk.LEFT,padx=5,pady=5)

        e1=tk.Entry(f0)
        e1.pack(side=tk.LEFT, fill=tk.X, expand=1,pady=5)

        if self.pgRange: #set pgRange if supplied
            e1.delete(0,tk.END)
            e1.insert(0,self.pgRange)


        f3=tk.Frame(self)
        f3.pack(fill=tk.X, padx=5, pady=5)
        okButton=tk.Button(f3,text='Rotate', command=rotate)
        okButton.pack(side=tk.RIGHT)

        cancelButton=tk.Button(f3,text='Cancel', command=onClosing)
        cancelButton.pack(side=tk.RIGHT)

        v.set(1)
        showChoice()

        self.bind('<Key-Escape>', lambda i: onEscape(i))
        self.protocol('WM_DELETE_WINDOW', onClosing)





