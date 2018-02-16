"""Environment Editor"""

from enum import Enum
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


class SelectionMode(Enum):
    MODE_NONE = 0
    MODE_SYSTEM = 1
    MODE_USER = 2
    MODE_COMMON = 3


class EnvFrame(tk.PanedWindow):
    def __init__(self, master, env):
        super().__init__(master, orient=tk.HORIZONTAL)
        self._master = master
        self._env = env
        self._tv_ids_system = {}
        self._tv_ids_user = {}
        self._tv_ids_shared = {}
        self._button_ids = {}

        self._tv = None
        self._mode = SelectionMode.MODE_NONE

        self._create_widgets()

        self.configure(bg="#66AFE0")
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky=tk.NSEW)

    def _update_treeview(self):
        system = self._tv.insert('', 'end', 'system', text='System')
        user = self._tv.insert('', 'end', 'user', text='User')
        common = self._tv.insert('', 'end', 'common', text='Common')

        for key in sorted(list(self._env.system.keys())):
            _id = self._tv.insert(system, 'end', text=key)
            self._tv_ids_system[_id] = key

        for key in sorted(list(self._env.user.keys())):
            _id = self._tv.insert(user, 'end', text=key)
            self._tv_ids_user[_id] = key

        for key in sorted(list(self._env.shared_variables())):
            _id = self._tv.insert(common, 'end', text=key)
            self._tv_ids_shared[_id] = key

    def _create_left_frame(self):
        _left = tk.Frame(self)

        _tv_frame = tk.Frame(_left)
        self._tv = ttk.Treeview(_tv_frame)
        self._tv.heading('#0', text="Environment Variables", anchor=tk.W)

        _tv_vsb = AutoScrollbar(_tv_frame, orient=tk.VERTICAL)
        _tv_vsb.configure(command=self._tv.yview)

        self._tv.configure(yscrollcommand=_tv_vsb.set)

        self._update_treeview()

        self._tv.grid(row=0, column=0, sticky=tk.NSEW)
        _tv_vsb.grid(row=0, column=1, sticky=(tk.NS, tk.E))

        _tv_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(4,4), pady=(2,2))
        _tv_frame.rowconfigure(0, weight=1)
        _tv_frame.rowconfigure(1, weight=0)
        _tv_frame.columnconfigure(0, weight=1)
        _tv_frame.columnconfigure(1, weight=0)

        _tv_button_frame = tk.Frame(_left)
        btn = ttk.Button(_tv_button_frame, text='Add', state='disabled')
        btn.grid(row=0, column=0, sticky=tk.W)
        self._button_ids['add_variable'] = btn
        btn = ttk.Button(_tv_button_frame, text='Delete', state='disabled')
        btn.grid(row=0, column=1, sticky=tk.W)
        self._button_ids['delete_variable'] = btn
        _tv_button_frame.grid(row=1, column=0, sticky=tk.W, padx=(4,4), pady=(2,2))
        _tv_button_frame.columnconfigure(0, weight=1)

        _left.configure(width=200)
        _left.columnconfigure(0, weight=1)
        _left.rowconfigure(0, weight=1)
        _left.rowconfigure(1, weight=0)
        _left.grid(row=0, column=0, sticky=(tk.NS, tk.W))

        self.add(_left, stretch='never')
        self.paneconfigure(_left, minsize=200)

        self._tv.bind('<<TreeviewSelect>>', self._tv_click)

    def _create_right_frame(self):
        _right = tk.Frame(self)

        self._element_frame = tk.Frame(_right)
        self._listbox = tk.Listbox(self._element_frame, relief=tk.FLAT)
        _listbox_vsb = AutoScrollbar(self._element_frame, orient=tk.VERTICAL)
        _listbox_vsb.configure(command=self._listbox.yview)
        _listbox_hsb = AutoScrollbar(self._element_frame, orient=tk.HORIZONTAL)
        _listbox_hsb.configure(command=self._listbox.xview)
        self._listbox.configure(yscrollcommand=_listbox_vsb.set, xscrollcommand=_listbox_hsb.set)

        self._listbox.bind('<<ListboxSelect>>', self._listbox_select)

        self._listbox.grid(row=0, column=0, sticky=tk.NSEW, padx=4, pady=2)
        _listbox_vsb.grid(row=0, column=1, sticky=(tk.NS, tk.E), padx=4, pady=2)
        _listbox_hsb.grid(row=1, column=0, sticky=(tk.S, tk.EW), padx=4, pady=2)

        self._element_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self._element_frame.columnconfigure(0, weight=1)
        self._element_frame.columnconfigure(1, weight=0)
        self._element_frame.rowconfigure(0, weight=1)
        self._element_frame.rowconfigure(1, weight=0)

        _button_frame = tk.Frame(_right)
        btn = ttk.Button(_button_frame, text="Edit", command=self._btn_edit, state='disabled')
        btn.grid(row=0, column=0, pady=2)
        self._button_ids['edit'] = btn
        btn = ttk.Button(_button_frame, text="Add", command=self._btn_add, state='disabled')
        btn.grid(row=1, column=0, pady=(12,2))
        self._button_ids['add'] = btn
        btn = ttk.Button(_button_frame, text="Delete", command=self._btn_delete, state='disabled')
        btn.grid(row=2, column=0, pady=2)
        self._button_ids['delete'] = btn
        btn = ttk.Button(_button_frame, text="Move Up", command=self._btn_move_up, state='disabled')
        btn.grid(row=4, column=0, pady=(12,2))
        self._button_ids['move_up'] = btn
        btn = ttk.Button(_button_frame, text="Move Down", command=self._btn_move_down, state='disabled')
        btn.grid(row=5, column=0, pady=2)
        self._button_ids['move_down'] = btn
        _button_frame.grid(row=0, column=1, sticky=(tk.NS, tk.E), padx=4, pady=2)

        _right.configure(width=200)
        _right.columnconfigure(0, weight=1)
        _right.columnconfigure(1, weight=0)
        _right.rowconfigure(0, weight=1)
        _right.grid(row=0, column=1, sticky=(tk.NS, tk.E), padx=4)

        self.add(_right, stretch='always')
        self.paneconfigure(_right, minsize=200)

    def _create_widgets(self):
        self._create_left_frame()
        self._create_right_frame()

    def _enable_button_by_id(self, id_):
        self._master.nametowidget(id_).configure(state='enabled')

    def _disable_button_by_id(self, id_):
        self._master.nametowidget(id_).configure(state='disabled')

    def _enable_button_by_name(self, name):
        self._enable_button_by_id(self._button_ids[name])

    def _disable_button_by_name(self, name):
        self._disable_button_by_id(self._button_ids[name])

    def _disable_all_buttons(self):
        for btn_id in self._button_ids.values():
            self._disable_button_by_id(btn_id)

    def _enable_all_buttons(self):
        for btn_id in self._button_ids.values():
            self._enable_button_by_id(btn_id)

    def _disable_variable_buttons(self):
        for name in ['add', 'edit', 'delete', 'move_up', 'move_down']:
            self._disable_button_by_name(name)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        if new_mode != self._mode:
            if new_mode == SelectionMode.MODE_COMMON:
                print('mode: common')
                self._mode_common()
            elif new_mode == SelectionMode.MODE_SYSTEM:
                print('mode: system')
                self._mode_variable()
            elif new_mode == SelectionMode.MODE_USER:
                print('mode: user')
                self._mode_variable()

            self._mode = new_mode

    def _mode_variable(self):
        for name in ['add_variable', 'delete_variable']:
            self._enable_button_by_name(name)

    def _mode_common(self):
        self._disable_all_buttons()

    def _mode_none(self):
        self._disable_all_buttons()

    def _tv_click(self, event=None):
        self._listbox.delete(0, tk.END)
        _id = self._tv.focus()
        self._disable_button_by_name('move_up')
        self._disable_button_by_name('move_down')
        value = None
        key = self._tv_ids_shared.get(_id, None)
        if key:
            env_values = self._env.get(key, location=EnvLocation.ENV_BOTH, exact=True)
            value = list(env_values.values())[0]
            self._mode = SelectionMode.MODE_COMMON
            self._mode_common()
            self._update_listbox(value, show_location=True)
        else:
            key = self._tv_ids_system.get(_id, None)
            if key:
                env_values = self._env.get(key, location=EnvLocation.ENV_SYSTEM, exact=True)
                value = list(env_values.values())[0]
                self._mode = SelectionMode.MODE_SYSTEM
                self._mode_variable()
                self._update_listbox(value)
            else:
                key = self._tv_ids_user.get(_id, None)
                if key:
                    env_values = self._env.get(key, location=EnvLocation.ENV_USER, exact=True)
                    value = list(env_values.values())[0]
                    self._mode = SelectionMode.MODE_USER
                    self._mode_variable()
                    self._update_listbox(value)
                else:
                    if _id == 'common':
                        self._mode = SelectionMode.MODE_COMMON
                        self._disable_all_buttons()
                    elif _id == 'system':
                        self._mode = SelectionMode.MODE_SYSTEM
                        self._enable_button_by_name('add_variable')
                        self._disable_button_by_name('delete_variable')
                    elif _id == 'user':
                        self._mode = SelectionMode.MODE_USER
                        self._enable_button_by_name('add_variable')
                        self._disable_button_by_name('delete_variable')

    def _update_listbox(self, value, show_location=False):
        _prefixes = {'system': 'S:', 'user': 'U:'}

        self._listbox.delete(0, tk.END)
        for _location, key in value.items():
            if isinstance(key.value, list):
                for item in key.value:
                    if show_location:
                        item = '%s %s' % (_prefixes[_location], item)
                    self._listbox.insert(tk.END, item)
            else:
                if show_location:
                    item = '%s %s' % (_prefixes[_location], key.value)
                else:
                    item = key.value
                self._listbox.insert(tk.END, item)

    def _listbox_select(self, event=None):
        if self._mode == SelectionMode.MODE_USER or self._mode == SelectionMode.MODE_SYSTEM:
            self._mode_variable()
            self._variable_select()

    def _variable_select(self):
        if self._mode == SelectionMode.MODE_COMMON or self._mode == SelectionMode.MODE_NONE:
            self._disable_all_buttons()

        for name in ['add', 'edit', 'delete']:
            self._enable_button_by_name(name)

        item_count = self._listbox.size()
        cur_selection = self._listbox.curselection()
        if cur_selection and item_count > 1:
            cur_selection = int(cur_selection[0])
            #start of list
            if cur_selection == 0:
                self._disable_button_by_name('move_up')
                self._enable_button_by_name('move_down')
            # end of list
            elif cur_selection == item_count - 1:
                self._enable_button_by_name('move_up')
                self._disable_button_by_name('move_down')
            else:
                self._enable_button_by_name('move_up')
                self._enable_button_by_name('move_down')
        else:
            self._disable_button_by_name('move_up')
            self._disable_button_by_name('move_down')


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


class EnvEditor():
    def __init__(self):
        self._root = tk.Tk()
        self._create_menu()

        bitmap_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'favicon.gif')
        if os.path.exists(bitmap_path):
            img = tk.PhotoImage(file=bitmap_path)
            self._root.iconphoto(True, img)

        if sys.platform == 'win32':
            self._store = WindowsEnvStore()
            self._root.title('Windows Environment Editor')

        self._frame = None

    def run(self):
        self._store.update()

        self._frame = EnvFrame(self._root, self._store.env)
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
            self._root.bind_all('<Control-Key-n>', self._command_new)
        elif 'darwin' in sys.platform:
            first_label = 'Env Editor'
            first_underline = -1
            new_underline = 0
            new_accel = 'Cmd + N'
            quit_label = 'Quit'
            quit_underline = 0
            quit_accel = 'Cmd + Q'
            self._root.bind_all('<Command-n>', self._command_new)
        elif 'linux' in sys.platform:
            first_label = 'File'
            first_underline = 0
            new_underline = 0
            new_accel = 'Ctrl + N'
            quit_label = 'Quit'
            quit_underline = 0
            quit_accel = 'Ctrl + Q'
            self._root.bind_all('<Control-Key-n>', self._command_new)

        menu = tk.Menu(self._root, tearoff=False)
        menu_file = tk.Menu(menu, tearoff=False)

        menu_file.add_command(label='New Variable...', command=self._command_new, accelerator=new_accel, underline=new_underline)

        menu_file.add_command(label='Import', command=self._command_import, underline=0)
        menu_file.add_command(label='Export', command=self._command_export, underline=0)
        menu_file.add_command(label=quit_label, command=self._command_exit, underline=quit_underline, accelerator=quit_accel)
        if first_underline != -1:
            menu.add_cascade(label=first_label, underline=first_underline, menu=menu_file)
        else:
            menu.add_cascade(label=first_label, menu=menu_file)
        self._root.configure(menu=menu)

    def _command_new(self, event=None):
        print('New')

    def _command_import(self, event=None):
        print('Import')

    def _command_export(self, event=None):
        print('Export')

    def _command_exit(self, event=None):
        self._root.destroy()
