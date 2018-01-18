from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import os.path

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk

try:
    from tkinter import font
except ImportError:
    import tkFont as font

try:
    from tkinter import ttk
except ImportError:
    import ttk


class EnvEditor():
    def __init__(self):
        self._root = tk.Tk()
        self._root.title('Environment Editor')

    def run(self):
        pass


class EnvStore():
    def __init__(self):
        self.type = 'system'
        self.location = ['HKLM', 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment']
        self.location = ['HKCU', 'Environment']
        self.location = ['bashrc', 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment']

    def parse(self):
        pass


class Env():
    def __init__(self):
        pass


if __name__ == '__main__':
    e = EnvEditor()
    e.run()
