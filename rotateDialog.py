"""
rotateDialog.py - Page rotation configuration dialog.

Allows users to rotate PDF pages by 90 or 180 degrees, either for all pages
or a specific page range.
"""

import tkinter as tk

from baseDialog import BaseDialog


class rotateDialog(BaseDialog):
    """Dialog for rotating PDF pages."""

    def __init__(self, parent, display, pgRange=None):
        super().__init__(parent, display, title="Rotation", pgRange=pgRange)

    def displayDialog(self):
        def rotate():
            """Apply rotation to selected pages."""
            if pageRangeVar.get() == 2:
                if not self.display.doc.parse_page_string(rangeEntry.get()):
                    return

            self.display.updatestatusBar('Rotating...')

            # Map selection to degrees
            rotation_map = {
                "Counterclockwise 90 degrees": -90,
                "Clockwise 90 degrees": 90,
                "180 degrees": 180
            }
            degrees = rotation_map.get(directionVar.get(), -90)

            if pageRangeVar.get() == 1:
                self.display.rotate(degrees)
            else:
                self.display.rotate(degrees, pgRange=rangeEntry.get())

            self.display.updatestatusBar('Finished rotating.')
            self.onClosing()

        def updateRangeState():
            """Enable/disable range entry based on selection."""
            if pageRangeVar.get() == 1:
                rangeEntry.configure(state='disabled')
            else:
                rangeEntry.configure(state='normal')

        # Direction selection
        dirFrame = tk.Frame(self)
        dirFrame.pack(fill=tk.X, padx=5)
        tk.Label(dirFrame, text='Direction:').pack(side=tk.LEFT, padx=5, pady=5)
        directionVar = tk.StringVar(value='Counterclockwise 90 degrees')
        rotationChoices = ['Counterclockwise 90 degrees', 'Clockwise 90 degrees', '180 degrees']
        tk.OptionMenu(dirFrame, directionVar, *rotationChoices).pack(
            side=tk.LEFT, fill=tk.X, expand=1, pady=5)

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
        tk.Button(buttonFrame, text='Rotate', command=rotate).pack(side=tk.RIGHT)
        tk.Button(buttonFrame, text='Cancel', command=self.onClosing).pack(side=tk.RIGHT)

        updateRangeState()
