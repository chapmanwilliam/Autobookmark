# -*- coding: utf-8 -*-
import queue
import os
import platform
import sys
import threading

import wx
import wx.adv

import action
import frame_main_gui


class FileDragAndDrop(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    # The following line is marked as "signature does not match" in the IDE but it works ...
    def OnDropFiles(self, x, y, file_paths):
        return self.window.launch_action(file_paths)


class FrameMain(frame_main_gui.FrameMain):
    def __init__(self, parent):
        frame_main_gui.FrameMain.__init__(self, parent)

        # Setup queuing (necessary to get communication to separate thread going).
        self.queue_gui_to_function = queue.Queue()
        self.queue_function_to_gui = queue.Queue()

        # Bind the "on close" event.
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Determine if the program is running frozen to an *.exe/*.app or from the Python interpreter.
        if hasattr(sys, 'frozen'):
            self.application_path = os.path.dirname(sys.executable)
        else:
            self.application_path = os.path.dirname(__file__)
        self.images_path = self.application_path + os.sep + 'images'

        # Set the application icon (unsupported on Mac OS X).
        if platform.system() != 'Darwin':
            ico = wx.Icon(self.images_path + os.sep + 'icon.ico', wx.BITMAP_TYPE_ICO)
            self.SetIcon(ico)

        # Adjust the background color of the static text widgets by manually specifying a color code in hex.
        self.background_color = '#e2e2e2'  # for background.png
        # self.background_color = '#ffffff'  # for background_alternative.png
        # Transparent background is not supported out of the box for static text but can be achieved:
        #  http://www.keacher.com/994/transparent-static-text-in-wxpython/
        #  http://stackoverflow.com/questions/2179173/wxpython-statictext-on-transparent-background
        self.DropHereStaticText.SetBackgroundColour(self.background_color)
        self.ProgressGaugeStaticText.SetBackgroundColour(self.background_color)
        self.ProgressGifStaticText.SetBackgroundColour(self.background_color)

        # Set the window title.
        self.SetTitle('AutoBookMarker')

        # Make the panel accept dropped objects.
        file_drop_target = FileDragAndDrop(self)
        self.DragDropPanel.SetDropTarget(file_drop_target)

        # Start the gif animation.
        # self.gui_add_gif_animation()

    def gui_update(self):
        try:
            self.Update()
            self.Refresh()
            self.Layout()
            self.Freeze()
            self.Thaw()
            return True
        except Exception as err:
            return False

    def gui_panel_background(self, event):
        dc = event.GetDC()
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.Clear()
        background_image = wx.Bitmap(self.images_path + os.sep + 'background.png')
        # background_image = wx.Bitmap(self.images_path + os.sep + 'background_alternative.png')
        dc.DrawBitmap(background_image, 0, 0)

    def gui_add_gif_animation(self):
        gif_sizer = self.ProgressGifStaticText.GetContainingSizer()
        ani = wx.adv.Animation(self.images_path + os.sep + 'spinner.gif')
        ctrl = wx.adv.AnimationCtrl(self.ProgressGifPanel, -1, ani)
        ctrl.SetBackgroundColour(self.background_color)
        ctrl.Play()
        gif_sizer.Insert(1, ctrl, 0, wx.ALIGN_CENTER | wx.ALL, 5)

    def launch_action(self, path_or_paths):
        # Check if one single path (dir picker) or a list of paths (file picker) were passed.
        paths = []
        if isinstance(path_or_paths, str):
            paths.append(path_or_paths)
        elif isinstance(path_or_paths, list):
            paths = path_or_paths

        # Switch from drag & drop target panel to progress indicator panel.
        self.switch_to_progress_panel('gauge')
        # self.switch_to_progress_panel('gif-spinner')

        # Launch the function that refreshes the status as well as the actual function that processes the files.
        thread_0 = threading.Thread(target=self.execute_threaded_function, name='launcher',
                                    args=(action.wait_some_time, paths))
        thread_0.daemon = False
        thread_0.start()

        return True

    def execute_threaded_function(self, function_to_call, objects_to_process):
        # Bind the window close event to cancel action function.
        self.Bind(wx.EVT_CLOSE, self.cancel_action)

        # Function to refresh the status.
        thread_1 = threading.Thread(target=self.refresh_status, name='status', args=())
        thread_1.daemon = True
        thread_1.start()

        # Function to process the files / folder.
        thread_2 = threading.Thread(target=function_to_call, name='function',
                                    args=(self.queue_gui_to_function, self.queue_function_to_gui, objects_to_process))
        thread_2.daemon = False
        thread_2.start()

        # Continue once thread_2 (the actual function) finishes.
        thread_2.join()

        # Bind the window close event to actually closing the window again.
        self.Bind(event=wx.EVT_CLOSE, handler=self.on_close)

        # Switch from progress indicator panel back to drag & drop target panel.
        self.switch_to_drag_drop_panel()

    def switch_to_progress_panel(self, type_of_progress_panel='gauge'):

        if type_of_progress_panel == 'gauge':
            self.DragDropPanel.Hide()
            self.ProgressGaugePanel.Show()
            self.ProgressGauge.Pulse()
        elif type_of_progress_panel == 'gif-spinner':
            self.DragDropPanel.Hide()
            self.ProgressGifPanel.Show()
            self.gui_update()

    def switch_to_drag_drop_panel(self):
        self.ProgressGaugePanel.Hide()
        self.ProgressGifPanel.Hide()
        self.DragDropPanel.Show()

    def refresh_status(self):
        self.ProgressGauge.SetValue(0)
        while True:
            try:
                # Store queue content in variable since reading an item from the queue also removes it from the queue.
                current_message = self.queue_gui_to_function.get()

                # Exit this loop as soon as a 'Finish', 'Cancel' or 'Error' message is found in queue.
                # Otherwise adjust the percentage value of the gauge or replace the text above it.
                if current_message == u'Finish':
                    break
                elif current_message.isdigit():
                    # Convention: If the value in the queue is a digit set the gauge to that value.
                    self.ProgressGauge.SetValue(int(current_message))
                    wx.Yield()
                    self.Layout()
                    self.GetParent().Layout()
                    self.Refresh()
                    self.Update()
                else:
                    # Convention: If value is a string (and not Finish/Error) replace the static text.
                    self.ProgressGaugeStaticText.SetLabel(current_message)
                    # self.ProgressGifStaticText.SetLabel(current_message)

            except Exception as err:  # PyDeadObjectError may appear when thread finishes.
                pass

    def cancel_action(self, event):
        self.queue_function_to_gui.put(u'Cancel', False)
        self.queue_gui_to_function.put(u'Cancelling...', False)

    def on_close(self, event):
        self.Destroy()
