# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Jun 17 2015)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import gettext

import wx

_ = gettext.gettext


###########################################################################
## Class FrameMain
###########################################################################

class FrameMain(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString, pos=wx.DefaultPosition,
                          size=wx.Size(-1, -1),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.STAY_ON_TOP | wx.SYSTEM_MENU | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        SizerMain = wx.BoxSizer(wx.VERTICAL)

        self.DragDropPanel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(190, 190), wx.TAB_TRAVERSAL)
        self.DragDropPanel.SetBackgroundColour(wx.Colour(255, 255, 255))

        PanelSizer = wx.BoxSizer(wx.VERTICAL)

        PanelSizer.AddSpacer(17)

        self.DropHereStaticText = wx.StaticText(self.DragDropPanel, wx.ID_ANY, _(u"\n\n\nDrop files here!"),
                                                wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTRE)
        self.DropHereStaticText.Wrap(-1)
        self.DropHereStaticText.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString))

        PanelSizer.Add(self.DropHereStaticText, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 0)

        self.DragDropPanel.SetSizer(PanelSizer)
        self.DragDropPanel.Layout()
        SizerMain.Add(self.DragDropPanel, 1, wx.ALL | wx.EXPAND, 0)

        self.ProgressGaugePanel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(190, 190), wx.TAB_TRAVERSAL)
        self.ProgressGaugePanel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.ProgressGaugePanel.Hide()

        PanelSizer = wx.BoxSizer(wx.VERTICAL)

        PanelSizer.AddSpacer(65)

        self.ProgressGaugeStaticText = wx.StaticText(self.ProgressGaugePanel, wx.ID_ANY, _(u"Please wait ..."),
                                                     wx.DefaultPosition, wx.DefaultSize, 0)
        self.ProgressGaugeStaticText.Wrap(-1)
        PanelSizer.Add(self.ProgressGaugeStaticText, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.ProgressGauge = wx.Gauge(self.ProgressGaugePanel, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size(130, -1),
                                      wx.GA_HORIZONTAL)
        self.ProgressGauge.SetValue(0)
        PanelSizer.Add(self.ProgressGauge, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.ProgressGaugePanel.SetSizer(PanelSizer)
        self.ProgressGaugePanel.Layout()
        SizerMain.Add(self.ProgressGaugePanel, 1, wx.EXPAND | wx.ALL, 0)

        self.ProgressGifPanel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(190, 190), wx.TAB_TRAVERSAL)
        self.ProgressGifPanel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.ProgressGifPanel.Hide()

        PanelSizer = wx.BoxSizer(wx.VERTICAL)

        PanelSizer.AddSpacer(50)

        self.ProgressGifStaticText = wx.StaticText(self.ProgressGifPanel, wx.ID_ANY, _(u"Please wait ..."),
                                                   wx.DefaultPosition, wx.DefaultSize, 0)
        self.ProgressGifStaticText.Wrap(-1)
        PanelSizer.Add(self.ProgressGifStaticText, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.ProgressGifPanel.SetSizer(PanelSizer)
        self.ProgressGifPanel.Layout()
        SizerMain.Add(self.ProgressGifPanel, 0, wx.EXPAND | wx.ALL, 0)

        self.SetSizer(SizerMain)
        self.Layout()
        SizerMain.Fit(self)

        self.Centre(wx.BOTH)

        # Connect Events
        self.DragDropPanel.Bind(wx.EVT_ERASE_BACKGROUND, self.gui_panel_background)
        self.ProgressGaugePanel.Bind(wx.EVT_ERASE_BACKGROUND, self.gui_panel_background)
        self.ProgressGifPanel.Bind(wx.EVT_ERASE_BACKGROUND, self.gui_panel_background)

    def __del__(self):
        pass

    # Virtual event handlers, overide them in your derived class
    def gui_panel_background(self, event):
        event.Skip()
