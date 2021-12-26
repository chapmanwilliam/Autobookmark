import tkinter as tk
from tkinter.filedialog import askopenfilename
import fitz
import sys


doc=None

def which(program):
    # http://stackoverflow.com/a/377028/3924118
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


class FilePrinterDialog(tk.Toplevel):

    def __init__(self, root, *args):
        global doc
        tk.Toplevel.__init__(self, root, *args)

        def onEscape(i):
            self.unbind('<Key-Escape>')
            self.root.focus_set()
            self.destroy()

        self.bind('<Key-Escape>',  lambda i : onEscape(i))
        self.doc=doc
        self.selected_file=None
        if self.doc:
            self.selected_file=self.doc.name
        self.root = root

        self.body = tk.Frame(self, bg="lightblue")
        self.body.pack(expand=True, fill="both")

#        self.title_frame = tk.Frame(self.body, pady=5)
#        self.title_frame.pack(fill="both", pady=(15, 5))

#        self.title = tk.Label(self.title_frame,  text="Let's print!")
#        self.title.pack(fill="x")

        # Current selected printer of your system
        self.system_default_destination = self._find_system_default_destination()

        # Finds printer names
        self.printers_names = self._find_printers_names()

        self.data_bytes = None  # Bytes read from the selected file to print
        self.selected_printer = None  # Hols name of selected printer

        # Display them
        self.printers_frame = tk.Frame(self.body, bg="lightblue", padx=10, pady=10)
        self.printers_frame.pack(expand=True, fill="both")
        self._display_printers()

        self.bottom_frame = tk.Frame(self.body, pady=5)
        self.bottom_frame.pack(fill="both", pady=(5, 16))

        #No copies
        self.lb1=tk.Label(self.bottom_frame, text='Copies:')
        self.lb1.pack(side='left', padx=10)
        self.spinCopies = tk.Spinbox(self.bottom_frame, from_=1, to=1000)
        self.spinCopies.pack(side='right', padx=10)

        #Page range
        self.bottomframe1=tk.Frame(self.body, pady=5)
        self.bottomframe1.pack(fill="both", pady=(5, 16))
        self.lb2=tk.Label(self.bottomframe1, text='Page Range:')
        self.lb2.pack(side='left', padx=10)
        self.edBoxPageRange = tk.Entry(self.bottomframe1)
        self.edBoxPageRange.pack(side='right', padx=10)

        #Double-sided
        self.bottomframe2=tk.Frame(self.body, pady=5)
        self.bottomframe2.pack(fill="both", pady=(5, 16))
        self.var1=tk.IntVar()
        self.dblSidedCheck=tk.Checkbutton(self.bottomframe2, variable=self.var1, text='Double sided')
        self.dblSidedCheck.pack(side='left', padx=10)



        #Print options
        self.finalFrame=tk.Frame(self.body, pady=5)
        self.finalFrame.pack(fill='both', pady=(5,16))
        self.print_file = tk.Button(self.finalFrame,
                                           text="Print",
                                           command=self._print_selected_file)


        self.print_file.pack()
#        self.print_file.pack(fill=tk.BOTH, padx=10)


        self._make_modal()



    def _read_file(self):
        # NOT USED!
        if not self.selected_file:
            raise ValueError("No file chosen")
        with open(self.selected_file, "rb") as in_file: # opening for [r]eading as [b]inary
            return in_file.read() # if you only wanted to read 512 bytes, do .read(512)

    def _print_selected_file(self):
        global doc
        if not self.selected_file:
            print("No file selected yet!")
        else:
            a = doc.parse_page_string(self.edBoxPageRange.get())  # list of pages to consider
            if a:
                newDoc=fitz.open()
                newDoc.insertPDF(doc)
                newDoc.select(a)
                newDoc.save('test.pdf')
                newDoc.close()

                options=[]
                options.append('lpr') #print command
                options.append('-r') #remove test file after
                options.append("-#"+str(self.spinCopies.get())) #no copies
                options.append('-o InputSlot=Tray2')
    #            if not self.edBoxPageRange.get()=="":
    #                options.append('-o page-ranges=' + self.edBoxPageRange.get())
                if self.var1.get():
                    options.append('-o sides=two-sided-long-edge')
                else:
                    options.append('-o sides=one-sided')
                options.append('test.pdf') #file to print
                subprocess.run(options)

    def _select_file(self):
        self.selected_file = askopenfilename(title = "Choose file to print")
        print(self.selected_file)

    def ongetOptionsPrinter(self):
        if self._find_current_selected_printer():
            # Sets the printer on your system
            print("Selected printer:", self.selected_printer)
            result= subprocess.run(["lpoptions", "-l", "-p", self.selected_printer],stdout=subprocess.PIPE).stdout.decode('utf-8')
            y=result.splitlines()
            options={}
            for l in y:
                z=l.split(':')
                options[z[0]]=z[1]
            return options
        else:
            print('No printer selected')
            return None


    def _on_listbox_selection(self, event):
        self.selected_printer = self._find_current_selected_printer()
        if self._find_current_selected_printer():
            # Sets the printer on your system
            subprocess.call(["lpoptions", "-d", self.selected_printer])
            print("Selected printer:", self.selected_printer)
            print(self.ongetOptionsPrinter())
        else:
            print('No printer selected')

    def _find_current_selected_printer(self):
        curselection = self.listbox.curselection()
        if len(curselection) > 0:
            return self.listbox.get(curselection[0])
        else:
            return None

    def _display_printers(self):
        self.scrollbar = tk.Scrollbar(self.printers_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(self.printers_frame,
                                  yscrollcommand=self.scrollbar.set,
                                  selectbackground="yellow",
                                  selectmode="single",
                                  height=6)

        for printer_name in self.printers_names:
            self.listbox.insert("end", printer_name)

        # Keep track of selected listbox
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_selection)

        # Sets first listbox as selected
        self.listbox.select_set(0) # Sets focus
        self.listbox.event_generate("<<ListboxSelect>>")

        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        self.listbox.configure(exportselection=False)

    def _find_system_default_destination(self):
        return subprocess.getoutput("lpstat -d").split(": ")[1]

    def _find_printers_names(self):
        # Command to obtain printer names based on: https://superuser.com/a/1016825/317323
        return subprocess.getoutput("lpstat -a | awk '{print $1}'").split("\n")

    def _make_modal(self):
        # Makes the window modal
        self.transient(self.root)
        self.grab_set()
        self.wait_window(self)


def printDialog(root, d):
    global doc
    if not d:
        return
    else:
        doc=d
    if not which("lpoptions") or not which("lpr") or not which("awk") or not which("lpstat"):
        sys.stderr.write("Requirements: lopotions, lpr, lpstat and awk not satisfied")
    else:
        FilePrinterDialog(root)
#        opener = tk.Button(root, text="Open printer chooser", command=lambda: FilePrinterDialog(root))
#        opener.pack()
