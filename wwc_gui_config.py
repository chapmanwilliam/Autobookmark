import fitz
from utilities import gettextselectedHighlights, selectWord, getWord, selectedAnnots, removeSelectedAnnots, \
    deselectAnnot, selectAnnot, inTextArea, isAnnotArea, parse_page_string, max_depth, get_labels_rule_dict, \
    add_default_label, getchar, remove_draw_links, draw_links, link_clicked, getselectSpans, select, removeSelection, \
    highlightSelection, getselectedText
import sys
import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

fitz.Document.parse_page_string = parse_page_string  # added WWC 10/1/21
fitz.Document.max_depth = max_depth  # added WWC 10/1/21
fitz.Document.get_labels_rule_dict = get_labels_rule_dict  # added WWC 10/1/21
fitz.Document.add_default_label = add_default_label  # added WWC 10/1/21
fitz.Page.getchar = getchar  # added WWC 22/1/21
fitz.Page.remove_draw_links = remove_draw_links  # added WWC 22/1/21
fitz.Page.draw_links = draw_links  # added WWC 22/1/21
fitz.Page.link_clicked = link_clicked  # added WWC 22/1/21
fitz.Page.getselectSpans = getselectSpans  # added WWC 22/1/21
fitz.Page.select = select  # added WWC 23/1/21
fitz.Page.removeSelection = removeSelection  # added WWC 23/1/21
fitz.Page.highlightSelection = highlightSelection  # added WWC 23/1/21
fitz.Page.getselectedText = getselectedText  # added WWC 23/1/21
fitz.Page.isAnnotArea = isAnnotArea  # added WWC 23/1/21
fitz.Page.inTextArea = inTextArea  # added WWC 23/1/21
fitz.Page.selectAnnot = selectAnnot  # added WWC 23/1/21
fitz.Page.deselectAnnot = deselectAnnot  # added WWC 23/1/21
fitz.Page.removeSelectedAnnots = removeSelectedAnnots  # added WWC 23/1/21
fitz.Page.selectedAnnots = selectedAnnots  # added WWC 23/1/21
fitz.Page.getWord = getWord  # added WWC 23/1/21
fitz.Page.selectWord = selectWord  # added WWC 23/1/21
fitz.Page.gettextselectedHighlights = gettextselectedHighlights  # added WWC 23/1/21

def getLocalResourcePath():
    if 'win32' in sys.platform:
        return os.path.abspath(os.curdir) + "\\Resources\\"
    elif 'darwin':
        return os.path.abspath(os.curdir) + "/Resources/"
    else:
        raise RuntimeError("Unsupported operating system")

print(getLocalResourcePath())

favicon_location = getLocalResourcePath()+"favicon.ico"
enter_location = getLocalResourcePath()+"enter.png"
book_location = getLocalResourcePath()+"book.png"
bookmark_location = getLocalResourcePath()+"bookmark.png"
table_location = getLocalResourcePath()+"table.png"
link_location = getLocalResourcePath()+"link.png"
asterisk_location = getLocalResourcePath()+"settings.png"
tree_location = getLocalResourcePath()+"pinetree"
close_location = getLocalResourcePath()+"close.png"
open_location = getLocalResourcePath()+"open.png"
save_location = getLocalResourcePath()+"save.png"
order_location = getLocalResourcePath()+"md-reload.png"
left_location = getLocalResourcePath()+"arrow-1-left.png"
right_location = getLocalResourcePath()+"arrow-1-right.png"
search_location = getLocalResourcePath()+"search.png"
print_location = getLocalResourcePath()+"print.png"
target_location = getLocalResourcePath()+"target.png"
delete_location = getLocalResourcePath()+"delete.png"
bookmark_tab_location = getLocalResourcePath()+"bookmark-alt.png"
documents_location = getLocalResourcePath()+"documents.png"
chrono_location = getLocalResourcePath()+"time.png"
anticlockwise_location = getLocalResourcePath()+"anticlockwise.png"
clockwise_location = getLocalResourcePath()+"clockwise.png"
settings_location = getLocalResourcePath()+"pyutilsettings.db"


class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """

    def __init__(self, widget, text='widget info'):
        self.waittime = 500  # miliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()
