"""
tocDialog.py - Table of Contents configuration dialog.

Allows users to create or remove a Table of Contents from the PDF document,
with options for title and depth level.
"""

import tkinter as tk

from baseDialog import BaseDialog
from wwc_TOC import write_toc, delete_toc, isTOC


class tocDialog(BaseDialog):
    """Dialog for creating and managing Table of Contents."""

    def __init__(self, parent, display):
        super().__init__(parent, display, title="Table of Contents")

    def displayDialog(self):
        def updateButtons():
            """Update button states based on whether TOC exists."""
            if isTOC(self.display.doc):
                okButton.config(text='Replace TOC')
                removeButton.config(state='normal')
            else:
                okButton.config(state='normal')
                removeButton.config(state='disabled')

        def getOptions():
            """Get current dialog options as dictionary."""
            return {
                "title": titleEntry.get(),
                "maxDepth": depthVar.get()
            }

        def setOptions(options):
            """Set dialog values from options dictionary."""
            titleEntry.delete(0, tk.END)
            titleEntry.insert(0, options['title'])
            max_doc_depth = self.display.doc.max_depth()
            if options['maxDepth'] <= max_doc_depth:
                depthVar.set(options['maxDepth'])
            else:
                depthVar.set(max_doc_depth)

        def getDefaults():
            """Get and save default options."""
            options = self.display.gettocdefaultOptions()
            self.display.savetocOptions(options)
            return options

        def addTOC():
            """Create TOC with current options."""
            self.display.updatestatusBar('Making TOC...')
            if write_toc(self.display.doc, getOptions(), self.display):
                self.onClosing()
                self.display.setPage(0)
                self.display.updatestatusBar('Finished TOC.')

        def removeTOC():
            """Remove existing TOC from document."""
            options = {'pgRange': titleEntry.get()}
            self.display.updatestatusBar('Removing TOC...')
            if delete_toc(self.display.doc, options, self.display):
                self.onClosing()
                self.display.setPgDisplay()
                self.display.updatestatusBar('Finished removing TOC.')

        # Title input
        titleFrame = tk.Frame(self)
        titleFrame.pack(fill=tk.X, padx=5)
        tk.Label(titleFrame, text='Title:').pack(side=tk.LEFT, padx=5, pady=5)
        titleEntry = tk.Entry(titleFrame)
        titleEntry.pack(side=tk.LEFT, fill=tk.X, expand=1, pady=5)

        # Depth selection
        depthFrame = tk.Frame(self)
        depthFrame.pack(fill=tk.X, padx=5)
        tk.Label(depthFrame, text='Depth:').pack(side=tk.LEFT, padx=5, pady=5)
        depthVar = tk.IntVar()
        depthChoices = list(range(1, self.display.doc.max_depth() + 1))
        depthOption = tk.OptionMenu(depthFrame, depthVar, *depthChoices)
        depthOption.pack(side=tk.LEFT, fill=tk.X, expand=1, pady=5)

        # Buttons
        buttonFrame = tk.Frame(self)
        buttonFrame.pack(fill=tk.X, padx=5, pady=5)
        okButton = tk.Button(buttonFrame, text='Add TOC', command=addTOC)
        okButton.pack(side=tk.RIGHT)
        removeButton = tk.Button(buttonFrame, text='Remove TOC', command=removeTOC)
        removeButton.pack(side=tk.RIGHT)
        tk.Button(buttonFrame, text='Cancel', command=self.onClosing).pack(side=tk.RIGHT)

        # Load saved options
        options = self.display.gettocOptions()
        if not options:
            options = getDefaults()
        setOptions(options)
        updateButtons()
