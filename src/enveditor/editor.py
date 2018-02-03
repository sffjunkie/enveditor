"""Environment Editor"""

import os.path
import sys
import tkinter as tk
from tkinter import ttk
from .envstore import WindowsEnvStore


class AutoScrollbar(ttk.Scrollbar):
    # http://effbot.org/zone/tkinter-autoscrollbar.htm
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError("cannot use pack with this widget")

    def place(self, **kw):
        raise tk.TclError("cannot use place with this widget")


class EnvFrame(tk.PanedWindow):
    def __init__(self, master, env):
        super().__init__(master, orient=tk.HORIZONTAL)
        self._env = env
        self._system_ids = {}
        self._user_ids = {}

        self.config(background="grey")

        self._tv = None
        self._tv_vsb = None
        self._create_widgets()
        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

    def _create_widgets(self):
        self._left = tk.Frame(self)

        self._tv = ttk.Treeview(self._left)
        self._tv.heading('#0', text="Environment Variables", anchor=tk.W)

        self._tv_vsb = AutoScrollbar(self._left, orient=tk.VERTICAL)
        self._tv_vsb.configure(command=self._tv.yview)

        self._tv.configure(yscrollcommand=self._tv_vsb.set)

        system = self._tv.insert('', 'end', 'system', text='System')
        for key, value in self._env.system.items():
            _id = self._tv.insert(system, 'end', text=key, values=value)
            self._system_ids[_id] = key

        user = self._tv.insert('', 'end', 'user', text='User')
        for key, value in self._env.user.items():
            _id = self._tv.insert(user, 'end', text=key)
            self._user_ids[_id] = key

        self._tv.grid(row=0, column=0, sticky=tk.NSEW)
        self._tv_vsb.grid(row=0, column=1, sticky=tk.NS)
        self._left.configure(width=200)
        self._left.columnconfigure(0, weight=1)
        self._left.columnconfigure(1, weight=0)
        self._left.rowconfigure(0, weight=1)
        self._left.grid(row=0, column=0, sticky=(tk.NS, tk.W))
        self.add(self._left, stretch='never')
        self.paneconfigure(self._left, minsize=200)

        self._right = tk.Frame(self)
        self._right.configure(width=200)
        self._right.columnconfigure(0, weight=1)
        self._right.rowconfigure(0, weight=1)
        self._right.grid(row=0, column=1, sticky=(tk.NS, tk.E))
        self.add(self._right, stretch='always')
        self.paneconfigure(self._right, minsize=200)

        self.configure(sashrelief=tk.RAISED, sashwidth=3, sashpad=3, bg="white")

        self._tv.bind('<<TreeviewSelect>>', self.tv_click)

    def tv_click(self, widget=None, event=None):
        _id = self._tv.focus()
        key = self._system_ids.get(_id, None)
        if key:
            print(_id, key, self._env.system[key])
        else:
            key = self._user_ids.get(_id, None)
            if key:
                print(_id, key, self._env.user[key])


class EnvEditor():
    def __init__(self):
        self._root = tk.Tk()

        bitmap_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'favicon.gif')
        if os.path.exists(bitmap_path):
            img = tk.PhotoImage(file=bitmap_path)
            self._root.iconphoto(True, img)

        if sys.platform == 'win32':
            self.store = WindowsEnvStore()
            self._root.title('Windows Environment Editor')
        self._frame = None

    def run(self):
        self.store.load()
        self._frame = EnvFrame(self._root, self.store.env)

        self._frame.grid(row=0, column=0, sticky=tk.NSEW)
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        width = int(self._root.winfo_screenwidth() / 2)
        height = int(self._root.winfo_screenheight() / 2)

        self._root.configure(width=width, height=height)
        self._root.mainloop()
