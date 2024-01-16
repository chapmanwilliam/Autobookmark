# -*- coding: utf-8 -*-
import time

from wwc_AutoBookmarker import externalDrop


def wait_some_time(queue_to_gui, queue_from_gui, file_path_list):
    file_path_list = [i for i in file_path_list if i.split('.')[-1].lower() == 'pdf']

    N = len(file_path_list)
    for i, file_path in enumerate(file_path_list):
        queue_to_gui.put(str(int(100.0 / N * i)), False)
        file = file_path.split('/')[-1]
        file = '.'.join(file.split('.')[:-1])
        if len(file) > 10:
            file = file[:10] + '...'
        queue_to_gui.put('Continuing ...\n{f}'.format(f=file), False)
        externalDrop(file_path)
        if not queue_from_gui.empty():
            if queue_from_gui.get() == u'Cancel':
                return

    queue_to_gui.put('100', False)
    time.sleep(0.5)

    queue_to_gui.put(u'Finish', False)
    return