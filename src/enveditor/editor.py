"""Environment Editor"""

from functools import partial
import os.path
import pprint
import sys
import tkinter as tk
from tkinter import ttk
from .envstore import WindowsEnvStore, EnvLocation


class AutoScrollbar(ttk.Scrollbar):
    # http://effbot.org/zone/tkinter-autoscrollbar.htm
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        # print(lo, hi)
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        super().set(lo, hi)

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
        self._shared_ids = {}

        self._tv = None
        self._tv_vsb = None
        self._create_widgets()
        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

    def _create_widgets(self):
        _left = tk.Frame(self)
        _tv_frame = tk.Frame(_left)

        self._tv = ttk.Treeview(_tv_frame)
        self._tv.heading('#0', text="Environment Variables", anchor=tk.W)

        _tv_vsb = AutoScrollbar(_tv_frame, orient=tk.VERTICAL)
        _tv_vsb.configure(command=self._tv.yview)

        self._tv.configure(yscrollcommand=_tv_vsb.set)

        system = self._tv.insert('', 'end', 'system', text='System')
        for key, value in self._env.system.items():
            _id = self._tv.insert(system, 'end', text=key, values=value)
            self._system_ids[_id] = key

        user = self._tv.insert('', 'end', 'user', text='User')
        for key, value in self._env.user.items():
            _id = self._tv.insert(user, 'end', text=key)
            self._user_ids[_id] = key

        common = self._tv.insert('', 'end', 'common', text='Common')
        for key in self._env.shared_keys():
            _id = self._tv.insert(common, 'end', text=key)
            self._shared_ids[_id] = key

        self._tv.grid(row=0, column=0, sticky=tk.NSEW)
        _tv_vsb.grid(row=0, column=1, sticky=(tk.NS, tk.E))

        _tv_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(4,4), pady=(2,2))
        _tv_frame.rowconfigure(0, weight=1)
        _tv_frame.columnconfigure(0, weight=1)
        _tv_frame.columnconfigure(1, weight=0)

        _tv_button_frame = tk.Frame(_left)
        btn = ttk.Button(_tv_button_frame, text="Add")
        btn.grid(row=0, column=0, sticky=tk.W)
        self._delete_btn = ttk.Button(_tv_button_frame, text="Delete", state='disabled')
        self._delete_btn.grid(row=0, column=1, sticky=tk.W)
        _tv_button_frame.grid(row=1, column=0, sticky=tk.W, padx=(4,4), pady=(2,2))
        _tv_button_frame.columnconfigure(0, weight=1)

        _left.configure(width=200)
        _left.columnconfigure(0, weight=1)
        _left.rowconfigure(0, weight=1)
        _left.rowconfigure(1, weight=0)
        _left.grid(row=0, column=0, sticky=(tk.NS, tk.W))

        self.add(_left, stretch='never')
        self.paneconfigure(_left, minsize=200)

        _right = tk.Frame(self)

        self._element_frame = tk.Frame(_right)
        self._listbox = tk.Listbox(self._element_frame, relief=tk.FLAT)
        _listbox_vsb = AutoScrollbar(self._element_frame, orient=tk.VERTICAL)
        _listbox_vsb.configure(command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=_listbox_vsb.set)

        self._listbox.grid(row=0, column=0, sticky=tk.NSEW, padx=4, pady=2)
        _listbox_vsb.grid(row=0, column=1, sticky=tk.NS, padx=4, pady=2)

        self._element_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self._element_frame.columnconfigure(0, weight=1)
        self._element_frame.columnconfigure(1, weight=0)
        self._element_frame.rowconfigure(0, weight=1)

        _button_frame = tk.Frame(_right)
        btn = ttk.Button(_button_frame, text="Add", command=self._btn_add)
        btn.grid(row=0, column=0, pady=2)
        btn = ttk.Button(_button_frame, text="Edit", command=self._btn_edit)
        btn.grid(row=1, column=0, pady=2)
        btn = ttk.Button(_button_frame, text="Delete", command=self._btn_delete)
        btn.grid(row=2, column=0, pady=2)
        btn = ttk.Button(_button_frame, text="Move Up", command=self._btn_move_up)
        btn.grid(row=4, column=0, pady=(12,2))
        btn = ttk.Button(_button_frame, text="Move Down", command=self._btn_move_down)
        btn.grid(row=5, column=0, pady=2)
        _button_frame.grid(row=0, column=1, sticky=(tk.NS, tk.E), padx=4, pady=2)

        _right.configure(width=200)
        _right.columnconfigure(0, weight=1)
        _right.columnconfigure(1, weight=0)
        _right.rowconfigure(0, weight=1)
        _right.grid(row=0, column=1, sticky=(tk.NS, tk.E), padx=4)

        self.add(_right, stretch='always')
        self.paneconfigure(_right, minsize=200)

        self.configure(bg="#66AFE0")

        self._tv.bind('<<TreeviewSelect>>', self._tv_click)

    def _tv_click(self, widget=None):
        _id = self._tv.focus()
        value = ''
        key = self._shared_ids.get(_id, None)
        if key:
            env_values = self._env.get(key)
            value = pprint.pformat(list(env_values.values()))
        else:
            key = self._system_ids.get(_id, None)
            if key:
                value = self._env.get(key, location=EnvLocation.ENV_SYSTEM)
                self._delete_btn.configure(state='enabled')
            else:
                key = self._user_ids.get(_id, None)
                if key:
                    value = self._env.get(key, location=EnvLocation.ENV_USER)
                    self._delete_btn.configure(state='enabled')
                else:
                    self._delete_btn.configure(state='disabled')

        if isinstance(value, list):
            self._fill_listbox(value)

    def _btn_add(self):
        pass

    def _btn_edit(self):
        pass

    def _btn_delete(self):
        pass

    def _btn_move_up(self):
        pass

    def _btn_move_down(self):
        pass

    def _fill_listbox(self, items):
        pass


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

        self._create_menu()

    def run(self):
        self.store.load()
        self._frame = EnvFrame(self._root, self.store.env)

        self._frame.grid(row=0, column=0, sticky=tk.NSEW)
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        width = int(self._root.winfo_screenwidth() / 2)
        height = int(self._root.winfo_screenheight() / 2)

        self._root.geometry('%dx%d+%d+%d' % (width, height, width/2, height/2))
        self._root.mainloop()

    def _create_menu(self):
        if 'win32' in sys.platform:
            first_label = 'File'
            first_underline = 0
            new_underline = 0
            new_accel = 'Ctrl + N'
            quit_label = 'Exit'
            quit_underline = 1
            quit_accel = 'Alt + F4'
        elif 'darwin' in sys.platform:
            first_label = 'Env Editor'
            first_underline = -1
            new_underline = 0
            new_accel = 'Cmd + N'
            quit_label = 'Quit'
            quit_underline = 0
            quit_accel = 'Cmd + Q'
        elif 'linux' in sys.platform:
            first_label = 'File'
            first_underline = 0
            new_underline = 0
            new_accel = 'Ctrl + N'
            quit_label = 'Quit'
            quit_underline = 0
            quit_accel = 'Ctrl + Q'

        menu = tk.Menu(self._root, tearoff=False)
        menu_file = tk.Menu(menu, tearoff=False)

        menu_file.add_command(label='New Variable...', command=self._command_new, accelerator=new_accel, underline=new_underline)
        self._root.bind_all('<Control-Key-n>', self._command_new)

        menu_file.add_command(label='Import', command=self._command_import, underline=0)
        menu_file.add_command(label='Export', command=self._command_export, underline=0)
        menu_file.add_command(label=quit_label, command=self._command_exit, underline=quit_underline, accelerator=quit_accel)
        if first_underline != -1:
            menu.add_cascade(label=first_label, underline=first_underline, menu=menu_file)
        else:
            menu.add_cascade(label=first_label, menu=menu_file)
        self._root.configure(menu=menu)

    def _btn_(self, event=None):
        print('command')

    def _command_new(self, event=None):
        print('New')

    def _command_import(self, event=None):
        print('Import')

    def _command_export(self, event=None):
        print('Export')

    def _command_exit(self, event=None):
        self._root.destroy()
