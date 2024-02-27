# Dependencies (packaged in exe) winshell customtkinter PYYaml
import os
import subprocess
import threading
import os.path
import requests
import datetime
import yaml
import sys
import customtkinter
import winshell
from win32com.client import Dispatch
import pythoncom

class UpdaterGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        pythoncom.CoInitialize()  # Initialize COM

        self.title("Modpack updater updater")
        self.geometry('400x300')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.info = customtkinter.CTkLabel(self, text='modpack updater installer',
                                           font=customtkinter.CTkFont(size=20, weight="bold"))
        self.info.grid(row=0, column=0, padx=20, pady=20, columnspan=2)
        self.subinfo = customtkinter.CTkLabel(self, text='Waiting for start')
        self.subinfo.grid(row=3, column=0, padx=20, pady=20, columnspan=2)
        self.progress = customtkinter.CTkProgressBar(self)
        self.progress.grid(row=4, column=0, padx=20, pady=20, sticky='ew', columnspan=2)
        self.create_shortcut = customtkinter.CTkCheckBox(self, text="Create Shortcut")
        self.create_shortcut.grid(row=1, column=0, padx=20, pady=20)
        self.create_shortcut.select()
        self.add_to_start = customtkinter.CTkCheckBox(self, text="Add to Start")
        self.add_to_start.grid(row=1, column=1, padx=20, pady=20)
        self.add_to_start.select()
        self.install_button = customtkinter.CTkButton(self, text="Install", command=self.install_in_thread)
        self.install_button.grid(row=2, column=0, padx=20, pady=20, columnspan=2)

    def __del__(self):
        pythoncom.CoUninitialize()  # Uninitialize COM when the instance is deleted

    def install_in_thread(self):
        # Call the download function in a new thread
        thread = threading.Thread(target=self.install)
        thread.start()

    def install(self):
        self.info.configure("Running Install/Update")
        self.progress.set(0)
        log.info('starting update')
        with open(r'temp/versions.yml') as versionlist:
            versions = yaml.load(versionlist, Loader=yaml.FullLoader)
        dividenumber = 1
        if versions['install']['add_files']:
            dividenumber += len(versions['install']['add_files'])
        to_add = 1 / dividenumber

        if versions['install']['add_files']:
            for filename in versions['install']['add_files']:
                self.progress.set(self.progress.get() + to_add)
                self.subinfo.configure(text=f"Downloading {filename}")
                r = requests.get(f"{versions['install']['url']}/{filename}",
                                 allow_redirects=False)
                if r.status_code == 200:
                    filename = f"C:/Program Files/Modpack installer/{filename}"
                    dirs, filenames = os.path.split(filename)
                    if dirs != '':
                        os.makedirs(dirs, exist_ok=True)
                    open(filename, 'wb').write(r.content)
                    log.info(f'Made file {filename}')
        self.progress.set(1)
        self.info.configure(text="Update Finished!")
        self.subinfo.configure(text="Done!")
        if self.create_shortcut.get():
            self.create_desktop_shortcut('C:/Program Files/Modpack installer/main.exe')
        if self.add_to_start.get():
            self.add_to_start_menu('C:/Program Files/Modpack installer/main.exe')
        self.install_button.configure(text="Launch Program", command=self.launch)

    def create_desktop_shortcut(self, exe_file):
        pythoncom.CoInitialize()  # Initialize COM
        try:
            desktop = winshell.desktop()
            path = os.path.join(desktop, 'modpack_installer' + '.lnk')
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = exe_file
            shortcut.save()
        finally:
            pythoncom.CoUninitialize()  # Uninitialize COM

    def add_to_start_menu(self, exe_file):
        pythoncom.CoInitialize()  # Initialize COM
        try:
            start_menu = winshell.start_menu()
            path = os.path.join(start_menu, 'modpack_installer' + '.lnk')
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = exe_file
            shortcut.save()
        finally:
            pythoncom.CoUninitialize()  # Uninitialize COM

    def launch(self):
        log.info('started program')
        subprocess.Popen(['C:/Program Files/Modpack installer/main.exe'], shell=True)
        sys.exit()

class ErrorGUI(customtkinter.CTk):
    def __init__(self, msg=str, err=str, time_wait=0, critical=False):
        super().__init__()

        self.title("ERROR!")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        arg_full = f"{msg}\nError:[{err}]"
        self.title = customtkinter.CTkLabel(self, text=str(arg_full))
        self.title.grid(row=0, column=0, columnspan=1, padx=20, pady=(20, 20))
        self.buttonframe = customtkinter.CTkFrame(self)
        self.buttonframe.grid(row=1, column=0)
        self.button = customtkinter.CTkButton(self.buttonframe, text="Exit", command=sys.exit)
        self.button.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="e")


class _cache(object):

    def __init__(self):
        self.data = {}

    def __setitem__(self, keys, item):
        self.data[keys] = [item]

    def __getitem__(self, keys):
        return self.data[keys][0]

    def getcount(self, keys):
        return self.data[keys][0]

    def listkeys(self):
        return list(self.data)

class file_logger():

    def __init__(self):
        self.cache = _cache()
        if not os.path.exists('logs'):
            os.mkdir('logs')

    def initialize(self, name: str, default=True, time=False):
        if not os.path.exists(f"logs/{name}"):
            os.mkdir(f"logs/{name}")
        if not time:
            time = self._get_time_now(True)
        info_log_file = f"logs/{name}/{time}_info.log"
        error_log_file = f"logs/{name}/{time}_errors.log"
        with open(info_log_file, 'a') as info_file, open(error_log_file, 'a') as error_file:
            self.cache['info', name] = info_log_file
            self.cache['error', name] = error_log_file
        if default:
            self.defaultlog = name
        return time

    def info(self, msg:str='No Message', name:str=None):
        if name is None:
            name = self.defaultlog
        with open(self.cache['info', name], 'a') as file:
            file.write(f"{self._get_time_now()} [INFO]  {msg}\n")
        print(f"{self._get_time_now()} [{name}][INFO]  {msg}")

    def warn(self, msg:str='No Message', err=False, name:str=None):
        errmsg = ''
        if name is None:
            name = self.defaultlog
        if err:
            errmsg = f"\n{self._get_time_now()} [ERMSG] {err}"
        with open(self.cache['info', name], 'a') as file:
            file.write(f"{self._get_time_now()} [WARN]  {msg}{errmsg}\n")
        print(f"{self._get_time_now()} [{name}][WARN]  {msg}{errmsg}")

    def error(self, msg:str='No Message', err:str='No Error', name:str=None):
        if name is None:
            name = self.defaultlog
        with open(self.cache['error', name], 'a') as file:
            file.write(f"{self._get_time_now()} [ERROR] {msg}\n{self._get_time_now()} [{name}][ERMSG] {err}\n")
        print(f"{self._get_time_now()} [{name}][ERROR] {msg}\n{self._get_time_now()} [{name}][ERMSG] {err}")

    def _get_time_now(self, filename=False):
        if filename:
            return datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        else:
            return datetime.datetime.now().strftime('%d-%m-%Y | %H:%M:%S')

def open_updater():
    updateapp = UpdaterGUI()
    updateapp.mainloop()

log = file_logger()
log.initialize(name='updater')

log.info(msg='Checking Version')
r = requests.get(f"https://origins.vmti.link/updater/client/installer/versions.yml",
                 allow_redirects=True)
if r.status_code == 200:
    if not os.path.exists('temp'):
        os.mkdir('temp')
    open('temp/versions.yml', 'wb').write(r.content)
    log.warn('Latest version not installed. Starting updater!')
    open_updater()

else:
    boot_error = True
    critical = True
    msg = "Connection to the mod server failed. Please check your internet connection or contact an admin"
    err = "no_200_response"
    log.warn(msg=msg, err=err)
    error_app = ErrorGUI(msg=str(msg), err=str(err))
    error_app.mainloop()
    sys.exit()