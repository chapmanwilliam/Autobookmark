"""
baseDialog.py - Base class for Tkinter dialog windows.

Provides common functionality shared across all dialog classes including
window setup, escape key handling, and proper cleanup on close.
"""

import tkinter as tk


class BaseDialog(tk.Toplevel):
    """
    Base dialog class providing common dialog functionality.

    Subclasses should override displayDialog() to create their specific UI.
    The base class handles:
    - Window initialization with parent and display references
    - Escape key binding to close the dialog
    - Proper cleanup on window close
    - Status bar updates
    """

    def __init__(self, parent, display, title="Dialog", pgRange=None):
        """
        Initialize the base dialog.

        Args:
            parent: Parent Tkinter widget
            display: Main display object for status updates and document access
            title: Window title (default: "Dialog")
            pgRange: Optional page range string for dialogs that need it
        """
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.display = display
        self.pgRange = pgRange

        self.title(title)
        self.attributes('-topmost', True)

        # Bind escape key and window close
        self.bind('<Key-Escape>', lambda e: self.onClosing())
        self.protocol('WM_DELETE_WINDOW', self.onClosing)

        self.displayDialog()

    def onClosing(self):
        """Handle dialog close - clear status bar and destroy window."""
        self.display.updatestatusBar("")
        self.destroy()

    def displayDialog(self):
        """
        Create the dialog UI. Override this method in subclasses.

        Subclasses should implement their specific dialog content here.
        """
        pass
