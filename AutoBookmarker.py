# -*- coding: utf-8 -*-
import sys

import wx

import frame_main


class AutoBookMarker(wx.App):
    def __init__(self):
        super(AutoBookMarker, self).__init__()
        self.frame = frame_main.FrameMain(None)
        self.SetTopWindow(self.frame)
        self.frame.Show()


if __name__ == '__main__':
    app = AutoBookMarker()
    app.MainLoop()
    sys.exit()
