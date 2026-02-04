"""
paginateDialog.py - PDF pagination configuration dialog.

Allows users to add or remove page numbers from PDF documents with
customizable position, font, size, style, and color options.
"""

import tkinter as tk

from baseDialog import BaseDialog
from wwc_paginatepdf import paginate, remove_pagination


class paginateDialog(BaseDialog):
    """Dialog for adding/removing page numbers from PDFs."""

    def __init__(self, parent, display, pgRange=None):
        super().__init__(parent, display, title="Pagination", pgRange=pgRange)

    def displayDialog(self):
        def removePagination():
            """Remove pagination from selected pages."""
            if pageRangeVar.get() == 2:
                if not self.display.doc.parse_page_string(rangeEntry.get()):
                    return
            options = getOptions()
            remove_pagination(self.display.doc, options, self.display)
            self.display.displayPage()
            self.display.savepaginationOptions(options)

        def doPaginate():
            """Add pagination to selected pages."""
            if pageRangeVar.get() == 2:
                if not self.display.doc.parse_page_string(rangeEntry.get()):
                    return
            options = getOptions()
            paginate(self.display.doc, options, self.display)
            self.display.displayPage()
            self.display.savepaginationOptions(options)

        def setOptions(options):
            """Set dialog values from options dictionary."""
            # Horizontal position
            hpos_map = {'L': 1, 'C': 2, 'R': 3}
            hPosVar.set(hpos_map.get(options['HPOS'], 1))

            # Vertical position
            vpos_map = {'T': 1, 'M': 2, 'B': 3}
            vPosVar.set(vpos_map.get(options['VPOS'], 3))

            # Margins
            vMarginEntry.delete(0, tk.END)
            vMarginEntry.insert(0, str(options['vMargin']))
            hMarginEntry.delete(0, tk.END)
            hMarginEntry.insert(0, str(options['hMargin']))

            # Style
            boldVar.set(options['bBold'])
            italicVar.set(options['bItalic'])
            fontVar.set(options['fontName'])
            colourVar.set(options['Colour'])
            fontSizeVar.set(options['Size'])

            # Page range
            rangeEntry.delete(0, tk.END)
            if options['pgRange']:
                rangeEntry.insert(0, options['pgRange'])
            pageRangeVar.set(1 if options['All'] else 2)

        def getDefaults():
            """Get and save default options."""
            options = self.display.getpaginationdefaultOptions()
            self.display.savepaginationOptions(options)
            return options

        def getOptions():
            """Get current dialog options as dictionary."""
            hpos_map = {1: 'L', 2: 'C', 3: 'R'}
            vpos_map = {1: 'T', 2: 'M', 3: 'B'}

            return {
                'HPOS': hpos_map[hPosVar.get()],
                'VPOS': vpos_map[vPosVar.get()],
                'vMargin': float(vMarginEntry.get()),
                'hMargin': float(hMarginEntry.get()),
                'bBold': boldVar.get(),
                'bItalic': italicVar.get(),
                'Colour': colourVar.get(),
                'fontName': fontVar.get(),
                'Size': fontSizeVar.get(),
                'pgRange': rangeEntry.get() if pageRangeVar.get() == 2 else None,
                'All': pageRangeVar.get() == 1
            }

        def resetDefaults():
            """Reset dialog to default values."""
            setOptions(getDefaults())

        def updateRangeState():
            """Enable/disable range entry based on selection."""
            rangeEntry.configure(state='disabled' if pageRangeVar.get() == 1 else 'normal')

        # Horizontal position and margin
        hFrame = tk.Frame(self)
        hFrame.pack(fill=tk.X, padx=5)
        hPosVar = tk.IntVar(value=1)
        tk.Radiobutton(hFrame, text='Left', variable=hPosVar, value=1).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Radiobutton(hFrame, text='Centre', variable=hPosVar, value=2).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Radiobutton(hFrame, text='Right', variable=hPosVar, value=3).pack(side=tk.LEFT, padx=5, pady=5)
        vMarginEntry = tk.Entry(hFrame)
        vMarginEntry.pack(side=tk.RIGHT, expand=1, fill=tk.X)
        tk.Label(hFrame, text='Margin (inches):').pack(side=tk.RIGHT, padx=5, pady=5)

        # Vertical position and margin
        vFrame = tk.Frame(self)
        vFrame.pack(fill=tk.X, padx=5)
        vPosVar = tk.IntVar(value=3)
        tk.Radiobutton(vFrame, text='Top', variable=vPosVar, value=1).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Radiobutton(vFrame, text='Middle', variable=vPosVar, value=2).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Radiobutton(vFrame, text='Bottom', variable=vPosVar, value=3).pack(side=tk.LEFT, padx=5, pady=5)
        hMarginEntry = tk.Entry(vFrame)
        hMarginEntry.pack(side=tk.RIGHT, expand=1, fill=tk.X)
        tk.Label(vFrame, text='Margin (inches):').pack(side=tk.RIGHT, padx=5, pady=5)

        # Font selection
        fontFrame = tk.Frame(self)
        fontFrame.pack(fill=tk.X, padx=5)
        tk.Label(fontFrame, text='Font:').pack(side=tk.LEFT, padx=5, pady=5)
        fontVar = tk.StringVar(value='Helvetica')
        fontChoices = ['Courier', 'Helvetica', 'Times Roman']
        tk.OptionMenu(fontFrame, fontVar, *fontChoices).pack(side=tk.LEFT, fill=tk.X, expand=1, pady=5)

        tk.Label(fontFrame, text='Size:').pack(side=tk.LEFT, padx=5, pady=5)
        fontSizeVar = tk.IntVar(value=12)
        tk.Spinbox(fontFrame, from_=8, to=60, textvariable=fontSizeVar).pack(
            side=tk.LEFT, fill=tk.X, expand=1, pady=5)

        # Style options
        styleFrame = tk.Frame(self)
        styleFrame.pack(fill=tk.X, padx=5)
        boldVar = tk.IntVar()
        tk.Checkbutton(styleFrame, text='Bold', variable=boldVar).pack(side=tk.LEFT)
        italicVar = tk.IntVar()
        tk.Checkbutton(styleFrame, text='Italic', variable=italicVar).pack(side=tk.LEFT)

        tk.Label(styleFrame, text='Colour:').pack(side=tk.LEFT, padx=5, pady=5)
        colourVar = tk.StringVar(value='Black')
        colourChoices = ['Black', 'Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Indigo', 'Violet']
        tk.OptionMenu(styleFrame, colourVar, *colourChoices).pack(side=tk.LEFT, fill=tk.X, expand=1, pady=5)

        # Page range selection
        rangeFrame = tk.LabelFrame(self, text='Page range')
        rangeFrame.pack(fill=tk.X, padx=5)
        pageRangeVar = tk.IntVar(value=1)
        tk.Radiobutton(rangeFrame, text='All', variable=pageRangeVar,
                       value=1, command=updateRangeState).pack(anchor=tk.W, padx=5, pady=5)
        tk.Radiobutton(rangeFrame, text='Page range:', variable=pageRangeVar,
                       value=2, command=updateRangeState).pack(side=tk.LEFT, padx=5, pady=5)
        rangeEntry = tk.Entry(rangeFrame)
        rangeEntry.pack(side=tk.LEFT, fill=tk.X, expand=1, pady=5)

        # Pre-fill page range if provided
        if self.pgRange:
            rangeEntry.delete(0, tk.END)
            rangeEntry.insert(0, self.pgRange)

        # Buttons
        buttonFrame = tk.Frame(self)
        buttonFrame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(buttonFrame, text='Paginate', command=doPaginate).pack(side=tk.RIGHT)
        tk.Button(buttonFrame, text='Remove pagination', command=removePagination).pack(side=tk.RIGHT)
        tk.Button(buttonFrame, text='Cancel', command=self.onClosing).pack(side=tk.RIGHT)
        tk.Button(buttonFrame, text='Set defaults', command=resetDefaults).pack(side=tk.LEFT)

        # Load saved options
        options = self.display.getpaginationOptions()
        if not options:
            options = getDefaults()
        setOptions(options)
