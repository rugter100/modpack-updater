# Dependencies: PYYaml customtkinter requests
# Custom libs: database logger

current_version = '1.1'


import subprocess
import os
import threading
import requests
import datetime
import yaml
import sys
import customtkinter
import libs.database as database
import libs.logger as logger

class BootGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Boot Info")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.info = customtkinter.CTkLabel(self, text='Starting application', font=customtkinter.CTkFont(size=20, weight="bold"))
        self.info.grid(row=0, column=0, padx=20, pady=20)
        self.subinfo = customtkinter.CTkLabel(self, text='Starting...')
        self.subinfo.grid(row=1, column=0, padx=20, pady=20)

    def updateinfo(self, arg="None"):
        self.info.configure(text=arg)

    def updatesubinfo(self, arg="None"):
        self.subinfo.configure(text=arg)

    def close_gui(self):
        self.destroy()


class ErrorGUI(customtkinter.CTk):
    def __init__(self, msg=str, err=str, time_wait=0, critical=False, updater=False):
        super().__init__()

        self.title("ERROR!")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        arg_part = "The program will still launch in"
        if updater:
            arg_part = "The Updater will run in"
        if not critical:
            arg_full = f"{msg}\nError:[{err}]\n{arg_part} {time_wait} seconds"
        else:
            arg_full = f"{msg}\nError:[{err}]\nThe program will exit in {time_wait} seconds"
        self.title = customtkinter.CTkLabel(self, text=str(arg_full))
        self.title.grid(row=0, column=0, columnspan=1, padx=20, pady=(20, 20))
        self.buttonframe = customtkinter.CTkFrame(self)
        self.buttonframe.grid(row=1, column=0)
        self.button = customtkinter.CTkButton(self.buttonframe, text="Exit", command=sys.exit)
        self.button.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="e")
        if not critical:
            self.button = customtkinter.CTkButton(self.buttonframe, text="Resume", command=self.skip_wait)
            self.button.grid(row=0, column=1, padx=20, pady=(20, 20), sticky="e")
        if updater:
            self.button.configure(command=self.launch_updater)

    def skip_wait(self):
        self.destroy()
        if not critical:
            open_second_gui()

    def launch_updater(self):
        subprocess.Popen(['updater.exe'], shell=True)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.entries_main = {}
        self.mysql_conn = False
        self.log = log
        self.info_cmdout = info_cmdout
        self.logging = logging

        self.current_date = datetime.datetime.now().date()

        with open(r'configs/config.yml') as config:
            self.cfg = yaml.load(config, Loader=yaml.FullLoader)

        with open(r'configs/info.yml') as info:
            info = yaml.load(info, Loader=yaml.FullLoader)

        with open(r'configs/forks.yml') as forklist:
            self.forks = yaml.load(forklist, Loader=yaml.FullLoader)

        self.sqdb = database.sqlite()
        self.sqdb.connect("configs/database.db")
        self.currentdb = self.sqdb

        self.title("Origins Mod updater")
        self.geometry(f"{800}x{500}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.set_install_dir = customtkinter.CTkButton(self.sidebar_frame, text="Set Install DIR", command=self.setinstalldir)
        self.set_install_dir.grid(row=23, column=0, padx=20, pady=(10,0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=25, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionmenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                       values=["System", "Light", "Dark",],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionmenu.grid(row=26, column=0, padx=20, pady=(10, 10))
        ui_scale = 100
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=27, column=0, padx=20, pady=(10, 0))
        self.scaling_optionmenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                               values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        customtkinter.set_widget_scaling(float(ui_scale) / 100)
        self.scaling_optionmenu.grid(row=28, column=0, padx=20, pady=(10, 20))
        self.scaling_optionmenu.set(f"{ui_scale}%")

        #Frame
        self.frame = customtkinter.CTkFrame(self)
        self.frame.grid(row=1, column=1, padx=(20, 0), pady=(0, 0), sticky='nsew')
        self.frame.rowconfigure(2, weight=1)
        self.frame.columnconfigure(11, weight=1)

        game_dir = self.sqdb.dict_getone('settings', 'game_dir')

        local_version = 'None'
        if os.path.exists(f"{game_dir[2]}/version.txt"):
            with open(f"{game_dir[2]}/version.txt", "r") as file:
                local_version = file.read()

        self.version_label = customtkinter.CTkLabel(self.frame, text=f"Current Version: {local_version}")
        self.version_label.grid(row=0, column=0, padx=20, pady=20, sticky='ew', columnspan=3)

        self.fork_select_label = customtkinter.CTkLabel(self.frame, text="Select Fork", font=('calibri', 20))
        self.fork_select_label.grid(row=1, column=0, padx=20, pady=(20, 10), sticky='ew')
        forklist = []
        for item in self.forks:
            forklist.append(self.forks[item]['name'])
        self.fork_select = customtkinter.CTkOptionMenu(self.frame, command=self.update_settings, values=forklist)
        self.fork_select.grid(row=2, column=0, padx=20, pady=10, sticky='ew')

        fork = self.sqdb.dict_getone('settings', 'fork')

        self.fork_select.set(self.forks[fork[2]]['name'])

        self.version_select_label = customtkinter.CTkLabel(self.frame, text="Select Version", font=('calibri', 20))
        self.version_select_label.grid(row=1, column=1, padx=20, pady=(20, 10), sticky='ew')
        versionlist = ['Latest']
        for item in info:
            versionlist.append(item)
        self.version_select = customtkinter.CTkOptionMenu(self.frame, command=self.update_settings, values=versionlist)
        self.version_select.grid(row=2, column=1, padx=20, pady=10, sticky='ew')

        version = self.sqdb.dict_getone('settings', 'version')
        self.version_select.set(version[2])

        self.update_modpack = customtkinter.CTkButton(self.frame, command=self.download_in_thread, text='Update')
        self.update_modpack.grid(row=1, column=2, padx=20, pady=10)

        self.loading_bar = customtkinter.CTkProgressBar(self.frame)
        self.loading_bar.grid(row=3, column=0, padx=20, pady=10, columnspan=3, sticky='ew')
        self.loading_bar.set(0)
        self.loading_bar_info = customtkinter.CTkLabel(self.frame, text='')
        self.loading_bar_info.grid(row=4, column=0, padx=20, pady=10, columnspan=3, sticky='ew')

        install_dir = self.sqdb.dict_getone('settings', 'game_dir')
        self.current_install_dir = customtkinter.CTkLabel(self.frame, text=f"Current Directory:\n{install_dir[2]}")
        self.current_install_dir.grid(row=25, column=0, padx=20, pady=10, columnspan=3)

        self.spacer_frame = customtkinter.CTkFrame(self.frame, height=20)
        self.spacer_frame.grid(row=50, column=0, columnspan=20, padx=0, pady=(20,0), sticky='sew')
        self.spacer_footer = customtkinter.CTkLabel(self.spacer_frame, text=f"Version: {current_version} | Copyright: © Vamting IT 2024", font=('calibri', 12))
        self.spacer_footer.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        if self.logging:
            self.log.info(msg='Main GUI Launched', cmdout=self.info_cmdout)

        if self.sqdb.fetchone('settings', filters="id=4")[2] == "dir/":
            self.setinstalldir()

    # Fully Functional | Has all logging
    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        self._log_info('Appearance Mode Changed')
        self.update_settings()

    # Fully Functional | Has all logging
    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)
        self._log_info('Scaling Changed')
        self.update_settings()

    def setinstalldir(self):
        success = False
        firsttry = True
        while not success:
            if firsttry:
                text = "Please paste your install DIR\n It should look something like this: \n\n C:/Users/Marije/AppData/Roaming/com.modrinth.theseus/profiles/Origins NoClient 3.1.1 \n\n (both \ and / are fine)"
                firsttry = False
            else:
                text = "ERROR! The directory you entered does not exist or entry is invalid! \n\nPlease paste your install DIR\n It should look something like this: \n\n C:/Users/Marije/AppData/Roaming/com.modrinth.theseus/profiles/Origins NoClient 3.1.1 \n\n (both \ and / are fine)"
            dialog = customtkinter.CTkInputDialog(text=text, title="Set Install Dir")
            output = str(dialog.get_input()).replace("\\", "/")
            if os.path.exists(output):
                self.sqdb.update('settings', 'value', output, filters="id=4")
                success = True
                self.current_install_dir.configure(text=f"Current Directory:\n{output}")
            else:

                self._log_error('The directory you entered is invalid or was not found!', err=f'path does not exist "{output}"')

    def update_settings(self, value=None): # Update settings to database
        appearance_mode = self.appearance_mode_optionmenu.get()
        scaling = self.scaling_optionmenu.get()
        forkname = self.fork_select.get()
        fork = 'base'
        for item in self.forks:
            if str(forkname) == str(self.forks[item]['name']):
                fork = item
                break
        version = self.version_select.get()
        desktopdata = {'appearance': appearance_mode, 'scaling': str(scaling.replace('%', '')), 'fork': fork, 'version': version}
        db_data = self.sqdb.dict_getall('settings')
        if db_data['appearance'][0] != desktopdata['appearance']:
            self.sqdb.update('settings', 'value', desktopdata['appearance'], f"id={db_data['appearance'][1]}")
        if db_data['scaling'][0] != desktopdata['scaling']:
            self.sqdb.update('settings', 'value', desktopdata['scaling'], f"id={db_data['scaling'][1]}")
        if db_data['fork'][0] != desktopdata['fork']:
            self.sqdb.update('settings', 'value', desktopdata['fork'], f"id={db_data['fork'][1]}")
            self.redownload_info(desktopdata['fork'])
        if db_data['version'][0] != desktopdata['version']:
            self.sqdb.update('settings', 'value', desktopdata['version'], f"id={db_data['version'][1]}")

    def redownload_info(self, fork:str):
        self._log_info('Updating modlist')
        r = requests.get(f"{self.cfg['user_preferences']['download_url']}/{self.forks[fork]['dir']}/info.yml",
                         allow_redirects=True)
        if r.status_code == 200:
            if os.path.exists('configs/info.yml'):
                os.remove('configs/info.yml')
            open('configs/info.yml', 'wb').write(r.content)
            with open(r'configs/info.yml') as info:
                info = yaml.load(info, Loader=yaml.FullLoader)
            versionlist = ['Latest']
            for item in info:
                versionlist.append(item)
            self.version_select.configure(values=versionlist)
        else:
            self._log_error("Connection to the mod server failed. Please check your internet connection or contact an admin", "no_200_response", True)

    def download_in_thread(self):
        # Call the download function in a new thread
        thread = threading.Thread(target=self.download)
        thread.start()

    def download(self, item=None):
        self._log_info('Starting download Process')
        sqdb = database.sqlite()
        sqdb.connect("configs/database.db")
        game_dir = sqdb.dict_getone('settings', 'game_dir')
        remote_version = self.version_select.get()
        forkname = self.fork_select.get()
        fork = 'base'
        for item in self.forks:
            if str(forkname) == str(self.forks[item]['name']):
                fork = item
                break
        if remote_version == 'Latest':
            remote_version = str(self.forks[fork]['latest_version'])
        with open(r'configs/info.yml') as info:
            info = yaml.load(info, Loader=yaml.FullLoader)
        local_version = False
        if os.path.exists(f"{game_dir[2]}/version.txt"):
            with open(f"{game_dir[2]}/version.txt", "r") as file:
                local_version = file.read().split('-')
        versions_to_update = [remote_version]
        if local_version:
            add_version = False
            for item in info:
                if add_version:
                    versions_to_update.append(item)
                if item == local_version[0]:
                    add_version = True
                    versions_to_update = [item]
                if item == remote_version:
                    add_version = False
        print(versions_to_update)
        for version in versions_to_update:
            self.loading_bar.set(0)
            dividenuber = 1
            if info[version]['added']:
                for type in info[version]['added']:
                    if info[version]['added'][type]:
                        for item in info[version]['added'][type]:
                            dividenuber += 1
            if info[version]['removed']:
                for type in info[version]['removed']:
                    if info[version]['removed'][type]:
                        for item in info[version]['removed'][type]:
                            dividenuber += 1
            loadingadd = 1 / dividenuber

            if info[version]['removed']:

                if info[version]['removed']['mods']:

                    for item in info[version]['removed']['mods']:
                        self.loading_bar_info.configure(text=f"Removing Mod {info[version]['removed']['mods'][item]['name']}")

                        if os.path.exists(f"{game_dir[2]}/mods/{info[version]['removed']['mods'][item]['file']}"):
                            os.remove(f"{game_dir[2]}/mods/{info[version]['removed']['mods'][item]['file']}")
                            self._log_info(f"Removed Shader '{info[version]['removed']['mods'][item]['name']}' as file '{info[version]['removed']['mods'][item]['file']}'")
                        else:
                            self._log_warn(f"Mod {info[version]['removed']['mods'][item]['name']} Was not found! Skipping", err=f"filenotfound: {info[version]['removed']['mods'][item]['file']}")
                        self.loading_bar.set(float(self.loading_bar.get() + loadingadd))



                if info[version]['removed']['shaders']:

                    for item in info[version]['removed']['shaders']:
                        self.loading_bar_info.configure(text=f"Removing Shader {info[version]['removed']['shaders'][item]['name']}")

                        if os.path.exists(f"{game_dir[2]}/shaderpacks/{info[version]['removed']['shaders'][item]['file']}"):
                            os.remove(f"{game_dir[2]}/shaderpacks/{info[version]['removed']['shaders'][item]['file']}")
                            self._log_info(f"Removed Shader '{info[version]['removed']['shaders'][item]['name']}' as file '{info[version]['removed']['shaders'][item]['file']}'")
                        else:
                            self._log_warn(f"Mod {info[version]['removed']['shaders'][item]['name']} Was not found! Skipping", err=f"filenotfound: {info[version]['removed']['mods'][item]['file']}")
                        self.loading_bar.set(float(self.loading_bar.get() + loadingadd))



                if info[version]['removed']['resourcepacks']:

                    for item in info[version]['removed']['resourcepacks']:
                        self.loading_bar_info.configure(text=f"Removing Mod {info[version]['removed']['resourcepacks'][item]['name']}")

                        if os.path.exists(f"{game_dir[2]}/resourcepacks/{info[version]['removed']['resourcepacks'][item]['file']}"):
                            os.remove(f"{game_dir[2]}/resourcepacks/{info[version]['removed']['resourcepacks'][item]['file']}")
                            self._log_info(f"Removed Resource Pack '{info[version]['removed']['resourcepacks'][item]['name']}' as file '{info[version]['removed']['resourcepacks'][item]['file']}'")
                        else:
                            self._log_warn(f"Resource pack {info[version]['removed']['resourcepacks'][item]['name']} Was not found! Skipping", err=f"filenotfound: {info[version]['removed']['mods'][item]['file']}")
                        self.loading_bar.set(float(self.loading_bar.get() + loadingadd))


            if info[version]['added']:
                self._log_info('Going through added mods')

                if info[version]['added']['mods']:
                    self._log_info('Going through mods')
                    if not os.path.exists(f"{game_dir[2]}/mods"):
                        os.mkdir(f"{game_dir[2]}/mods")

                    for item in info[version]['added']['mods']:
                        self._log_info(f"Checking Mod {info[version]['added']['mods'][item]['name']}")
                        self.loading_bar_info.configure(text=f"Checking Mod {info[version]['added']['mods'][item]['name']}")

                        if not os.path.exists(f"{game_dir[2]}/mods/{info[version]['added']['mods'][item]['file']}"):
                            self.loading_bar_info.configure(text=f"Installing Mod {info[version]['added']['mods'][item]['name']}")
                            r = requests.get(info[version]['added']['mods'][item]['url'], allow_redirects=True)

                            if r.status_code == 200:
                                open(f"{game_dir[2]}/mods/{info[version]['added']['mods'][item]['file']}", 'wb').write(r.content)
                                self._log_info(f"Installed Mod '{game_dir[2]}/mods/{info[version]['added']['mods'][item]['name']}' as file '{game_dir[2]}/mods/{info[version]['added']['mods'][item]['file']}'")
                        self.loading_bar.set(float(self.loading_bar.get() + loadingadd))



                if info[version]['added']['shaders']:
                    self._log_info('Going through shaders')
                    if not os.path.exists(f"{game_dir[2]}/shaders"):
                        os.mkdir(f"{game_dir[2]}/shaders")

                    for item in info[version]['added']['shaders']:
                        self._log_info(f"Checking Shader {info[version]['added']['shaders'][item]['name']}")
                        self.loading_bar_info.configure(text=f"Checking Shader {info[version]['added']['shaders'][item]['name']}")

                        if not os.path.exists(f"{game_dir[2]}/shaderpacks/{info[version]['added']['shaders'][item]['file']}"):
                            self.loading_bar_info.configure(text=f"Installing Shader {info[version]['added']['shaders'][item]['name']}")
                            r = requests.get(info[version]['added']['shaders'][item]['url'], allow_redirects=True)

                            if r.status_code == 200:
                                open(f"{game_dir[2]}/shaderpacks/{info[version]['added']['shaders'][item]['file']}", 'wb').write(r.content)
                                self._log_info(f"Installed Shader '{info[version]['added']['shaders'][item]['name']}' as file '{game_dir[2]}/mods/{info[version]['added']['shaders'][item]['file']}'")
                        self.loading_bar.set(float(self.loading_bar.get() + loadingadd))



                if info[version]['added']['resourcepacks']:
                    self._log_info('Going through resouce packs')
                    if not os.path.exists(f"{game_dir[2]}/resourcepacks"):
                        os.mkdir(f"{game_dir[2]}/resourcepacks")

                    for item in info[version]['added']['resourcepacks']:
                        self._log_info(f"Checking Resource pack {info[version]['added']['resourcepacks'][item]['name']}")
                        self.loading_bar_info.configure(text=f"Checking Resource pack {info[version]['added']['resourcepacks'][item]['name']}")

                        if not os.path.exists(f"{game_dir[2]}/resourcepacks/{info[version]['added']['resourcepacks'][item]['file']}"):
                            self.loading_bar_info.configure(text=f"Installing Resource Pack {info[version]['added']['resourcepacks'][item]['name']}")
                            r = requests.get(info[version]['added']['resourcepacks'][item]['url'], allow_redirects=True)

                            if r.status_code == 200:
                                open(f"{game_dir[2]}/resourcepacks/{info[version]['added']['resourcepacks'][item]['file']}", 'wb').write(r.content)
                                self._log_info(f"Installed Resouce Pack '{info[version]['added']['resourcepacks'][item]['name']}' as file '{game_dir[2]}/mods/{info[version]['added']['resourcepacks'][item]['file']}'")
                        self.loading_bar.set(float(self.loading_bar.get() + loadingadd))

                if info[version]['added']['other_data']:
                    self._log_info('Going through other data')

                    for item in info[version]['added']['other_data']:
                        self._log_info(f"Checking file {info[version]['added']['other_data'][item]['file']}")
                        self.loading_bar_info.configure(text=f"Checking File {info[version]['added']['other_data'][item]['file']}")
                        if info[version]['added']['other_data'][item]['replace']:
                            if os.path.exists(f"{game_dir[2]}/{info[version]['added']['other_data'][item]['file']}"):
                                os.remove(f"{game_dir[2]}/{info[version]['added']['other_data'][item]['file']}")

                        if not os.path.exists(f"{game_dir[2]}/{info[version]['added']['other_data'][item]['file']}"):
                            self.loading_bar_info.configure(text=f"Installing File {info[version]['added']['other_data'][item]['file']}")
                            r = requests.get(info[version]['added']['other_data'][item]['url'], allow_redirects=True)

                            if r.status_code == 200:
                                open(f"{game_dir[2]}/{info[version]['added']['resourcepacks'][item]['file']}", 'wb').write(r.content)
                                self._log_info(f"Installed Extra file '{info[version]['added']['other_data'][item]['file']}'")
                        self.loading_bar.set(float(self.loading_bar.get() + loadingadd))

            self.loading_bar.set(1)
            self.loading_bar_info.configure(text="Done!")
        if os.path.exists(f"{game_dir[2]}/version.txt"):
            os.remove(f"{game_dir[2]}/version.txt")
        with open(f"{game_dir[2]}/version.txt", "w") as file:
            file.write(f"{remote_version}-{fork}")


    # Not Functional yet !!DO NOT CALL!!
    def open_modlist(self):
        # create scrollable frame and variables
        self.grid_rowconfigure(0, weight=1)
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.grid_rowconfigure(0, weight=0)
        self.tabview.grid_columnconfigure(0, weight=1)

        self.tabview.add('Mods')
        self.tabview.tab('Mods').grid_rowconfigure(0, weight=1)
        self.tabview.tab('Mods').grid_columnconfigure(0, weight=1)
        self.scrollable_frame_mods = customtkinter.CTkScrollableFrame(self.tabview.tab('Mods'))
        self.scrollable_frame_mods.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.mods_list_1 = customtkinter.CTkFrame(self.scrollable_frame_mods)
        self.mods_list_1.grid(row=0, column=0, sticky='nsw', padx=5)
        self.mods_list_1.rowconfigure(100, weight=0)
        self.mods_list_legend_1 = customtkinter.CTkButton(self.mods_list_1, text='Name',
                                                          text_color_disabled="white", state="disabled")
        self.mods_list_legend_1.grid(row=0, column=0, sticky='ew')

        self.mods_list_2 = customtkinter.CTkFrame(self.scrollable_frame_mods)
        self.mods_list_2.grid(row=0, column=1, sticky='nsw', padx=5)
        self.mods_list_2.rowconfigure(100, weight=0)
        self.mods_list_legend_2 = customtkinter.CTkButton(self.mods_list_2, text='Version',
                                                          text_color_disabled="white", state="disabled")
        self.mods_list_legend_2.grid(row=0, column=0, sticky='ew')

        self.mods_list_3 = customtkinter.CTkFrame(self.scrollable_frame_mods)
        self.mods_list_3.grid(row=0, column=2, sticky='nsw', padx=5)
        self.mods_list_3.rowconfigure(100, weight=0)
        self.mods_list_legend_3 = customtkinter.CTkButton(self.mods_list_3, text='Shortname',
                                                          text_color_disabled="white", state="disabled")
        self.mods_list_legend_3.grid(row=0, column=0, sticky='ew')

        self.mods_list_4 = customtkinter.CTkFrame(self.scrollable_frame_mods)
        self.mods_list_4.grid(row=0, column=3, sticky='nsw', padx=5)
        self.mods_list_4.rowconfigure(100, weight=0)
        self.mods_list_legend_4 = customtkinter.CTkButton(self.mods_list_4, text='Added/Removed',
                                                          text_color_disabled="white", state="disabled")
        self.mods_list_legend_4.grid(row=0, column=0, sticky='ew')

        self.mods_data_1 = {}
        self.mods_data_2 = {}
        self.mods_data_3 = {}
        self.mods_data_4 = {}

        self.tabview.add('Resource Packs')
        self.tabview.tab('Resource Packs').grid_rowconfigure(0, weight=1)
        self.tabview.tab('Resource Packs').grid_columnconfigure(0, weight=1)
        self.scrollable_frame_resource_packs = customtkinter.CTkScrollableFrame(self.tabview.tab('Resource Packs'))
        self.scrollable_frame_resource_packs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.resource_pack_list_1 = customtkinter.CTkFrame(self.scrollable_frame_resource_packs)
        self.resource_pack_list_1.grid(row=0, column=0, sticky='nsw', padx=5)
        self.resource_pack_list_1.rowconfigure(100, weight=0)
        self.resource_pack_list_legend_1 = customtkinter.CTkButton(self.resource_pack_list_1, text='Name',
                                                                   text_color_disabled="white", state="disabled")
        self.resource_pack_list_legend_1.grid(row=0, column=0, sticky='ew')

        self.resource_pack_list_2 = customtkinter.CTkFrame(self.scrollable_frame_resource_packs)
        self.resource_pack_list_2.grid(row=0, column=1, sticky='nsw', padx=5)
        self.resource_pack_list_2.rowconfigure(100, weight=0)
        self.resource_pack_list_legend_2 = customtkinter.CTkButton(self.resource_pack_list_2, text='Version',
                                                                   text_color_disabled="white", state="disabled")
        self.resource_pack_list_legend_2.grid(row=0, column=0, sticky='ew')

        self.resource_pack_list_3 = customtkinter.CTkFrame(self.scrollable_frame_resource_packs)
        self.resource_pack_list_3.grid(row=0, column=2, sticky='nsw', padx=5)
        self.resource_pack_list_3.rowconfigure(100, weight=0)
        self.resource_pack_list_legend_3 = customtkinter.CTkButton(self.resource_pack_list_3, text='Shortname',
                                                                   text_color_disabled="white", state="disabled")
        self.resource_pack_list_legend_3.grid(row=0, column=0, sticky='ew')

        self.resource_pack_list_4 = customtkinter.CTkFrame(self.scrollable_frame_resource_packs)
        self.resource_pack_list_4.grid(row=0, column=3, sticky='nsw', padx=5)
        self.resource_pack_list_4.rowconfigure(100, weight=0)
        self.resource_pack_list_legend_4 = customtkinter.CTkButton(self.resource_pack_list_4, text='Added/Removed',
                                                                   text_color_disabled="white", state="disabled")
        self.resource_pack_list_legend_4.grid(row=0, column=0, sticky='ew')

        self.resource_pack_data_1 = {}
        self.resource_pack_data_2 = {}
        self.resource_pack_data_3 = {}
        self.resource_pack_data_4 = {}

        self.tabview.add('Shaders')
        self.tabview.tab('Shaders').grid_rowconfigure(0, weight=1)
        self.tabview.tab('Shaders').grid_columnconfigure(0, weight=1)
        self.scrollable_frame_shaders = customtkinter.CTkScrollableFrame(self.tabview.tab('Shaders'))
        self.scrollable_frame_shaders.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.shaders_list_1 = customtkinter.CTkFrame(self.scrollable_frame_shaders)
        self.shaders_list_1.grid(row=0, column=0, sticky='nsw', padx=5)
        self.shaders_list_1.rowconfigure(100, weight=0)
        self.shaders_list_legend_1 = customtkinter.CTkButton(self.shaders_list_1, text='Name',
                                                             text_color_disabled="white", state="disabled")
        self.shaders_list_legend_1.grid(row=0, column=0, sticky='ew')

        self.shaders_list_2 = customtkinter.CTkFrame(self.scrollable_frame_shaders)
        self.shaders_list_2.grid(row=0, column=1, sticky='nsw', padx=5)
        self.shaders_list_2.rowconfigure(100, weight=0)
        self.shaders_list_legend_2 = customtkinter.CTkButton(self.shaders_list_2, text='Version',
                                                             text_color_disabled="white", state="disabled")
        self.shaders_list_legend_2.grid(row=0, column=0, sticky='ew')

        self.shaders_list_3 = customtkinter.CTkFrame(self.scrollable_frame_shaders)
        self.shaders_list_3.grid(row=0, column=2, sticky='nsw', padx=5)
        self.shaders_list_3.rowconfigure(100, weight=0)
        self.shaders_list_legend_3 = customtkinter.CTkButton(self.shaders_list_3, text='Shortname',
                                                             text_color_disabled="white", state="disabled")
        self.shaders_list_legend_3.grid(row=0, column=0, sticky='ew')

        self.shaders_list_4 = customtkinter.CTkFrame(self.scrollable_frame_resource_packs)
        self.shaders_list_4.grid(row=0, column=3, sticky='nsw', padx=5)
        self.shaders_list_4.rowconfigure(100, weight=0)
        self.shaders_list_legend_4 = customtkinter.CTkButton(self.shaders_list_4, text='Added/Removed',
                                                             text_color_disabled="white", state="disabled")
        self.shaders_list_legend_4.grid(row=0, column=0, sticky='ew')

        self.shaders_data_1 = {}
        self.shaders_data_2 = {}
        self.shaders_data_3 = {}
        self.shaders_data_4 = {}

    def error_message(self, msg="No Error", err="Unknown error"):
        self.error_messageTL = customtkinter.CTkToplevel(self)
        self.error_messageTL.title("ERROR!")
        self.error_messageTL.grid_columnconfigure(0, weight=1)
        self.error_messageTL.grid_rowconfigure(0, weight=1)
        arg_full = f"{msg}\nError:[{err}]"
        title = customtkinter.CTkLabel(self.error_messageTL, text=str(arg_full))
        title.grid(row=0, column=0, padx=20, pady=(20, 5))
        button = customtkinter.CTkButton(self.error_messageTL, text="Ok", command=self.error_messageTL.destroy)
        button.grid(row=1, column=0, padx=20, pady=(5, 20))
        self.error_messageTL.grab_set_global()

    # Functional as far as needed
    def info_message(self, msg="No Info", update=False):
        if update:
            self.info_messageTL_title.configure(text=msg)
        else:
            self.info_messageTL = customtkinter.CTkToplevel(self)
            self.info_messageTL.title("Info")
            self.info_messageTL.grid_columnconfigure(0, weight=1)
            self.info_messageTL.grid_rowconfigure(0, weight=1)
            self.info_messageTL_title = customtkinter.CTkLabel(self.info_messageTL, text=msg)
            self.info_messageTL_title.grid(row=0, column=0, padx=20, pady=(20, 5))
            self.info_messageTL_button = customtkinter.CTkButton(self.info_messageTL, text="Ok",
                                                                 command=self.info_messageTL.destroy)
            self.info_messageTL_button.grid(row=1, column=0, padx=20, pady=(5, 20))
            self.info_messageTL.grab_set()

    def _log_info(self, msg:str, popup=False, updatepopup=False):
        if self.logging:
            self.log.info(name='desktop', msg=msg, cmdout=self.info_cmdout)
        if popup:
            self.info_message(msg=msg, update=updatepopup)

    def _log_warn(self, msg:str, err=False, popup=False, updatepopup=False):
        if self.logging:
            self.log.warn(name='desktop', msg=msg, err=err, cmdout=self.info_cmdout)
        if popup:
            self.info_message(msg=msg, update=updatepopup)

    def _log_error(self, msg:str, err:str='No Error', popup=False):
        if self.logging:
            self.log.info(name='desktop', msg=msg, cmdout=self.info_cmdout)
        if popup:
            self.error_message(msg=msg, err=err)

def open_second_gui():
    app = App()
    app.mainloop()

def bootgui():
    bootapp = BootGUI()
    bootapp.mainloop()

def launch_updater():
    subprocess.Popen(['updater.exe'], shell=True)


if __name__ == "__main__":
    log = logger.file_logger()
    log_time = log.initialize('desktop')
    customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"
    boot_error = False
    critical = False
    msg = "error message was called accidentally"
    err = False
    update = False
    mysql_connected = False
    timetowait = 30

    bootapp = BootGUI()

    with open(r'configs/config.yml') as config:
        cfg = yaml.load(config, Loader=yaml.FullLoader)

        bootapp.updateinfo("Checking configs")
        bootapp.updatesubinfo("checking config.yml")
        bootapp.update()  # Force an update of the GUI
        if cfg['user_preferences']['logging']:
            log.info(msg='Scanning configs/config.yml for valid entries', cmdout=cfg['user_preferences']['info_cmdout'])

        # checks if config entries are valid
        bool_values = {'debug': cfg['debug'],
                       'init_db': cfg['init_db'],
                       'user_preferences/logging': cfg['user_preferences']['logging'],
                       'user_preferences/info_cmdout': cfg['user_preferences']['info_cmdout']}

        str_values = {'download_url': cfg['user_preferences']['download_url']}

        # int_values = {'':1}

        for key, value in bool_values.items():
            if not isinstance(value, bool):
                boot_error = True
                critical = True
                msg = "An error occurred with config.yml"
                err = f"{key} is not a boolean (True/False)"
                break

        if not boot_error:
            for key, value in str_values.items():
                if not isinstance(value, str):
                    boot_error = True
                    critical = True
                    msg = "An error occurred with config.yml"
                    err = f"{key} is not a string (make sure to put value in between '')"
                    break

        """if not boot_error:
            for key, value in int_values.items():
                if not isinstance(value, int):
                    boot_error = True
                    critical = True
                    msg = "An error occurred with config.yml"
                    err = f"{key} is not a integer (numeric digit)"
                    break"""

        logging = cfg['user_preferences']['logging']
        info_cmdout = cfg['user_preferences']['info_cmdout']

        if not boot_error:
            log.info(msg='Checking Version', cmdout=info_cmdout)
            r = requests.get(f"{cfg['user_preferences']['download_url']}/installer/versions.yml",
                             allow_redirects=True)
            if r.status_code == 200:
                open('configs/versions.yml', 'wb').write(r.content)
                with open(r'configs/versions.yml') as versionlist:
                    versions = yaml.load(versionlist, Loader=yaml.FullLoader)
                latest_version = list(versions.keys())[-1]

                if str(current_version) != str(latest_version):
                    boot_error = True
                    critical = False
                    msg = "You do not have the latest version of the updater installed. please check origins.vmti.link or the discord for an update"
                    err = f"Your version: {current_version} | Latest version: {latest_version}"
                    update = True
                    log.warn('Latest version not installed. Starting updater!')

            else:
                boot_error = True
                critical = True
                msg = "Connection to the mod server failed. Please check your internet connection or contact an admin"
                err = "no_200_response"

        if not boot_error:
            if logging:
                log.info(msg='Scan successful! Connecting to database', cmdout=info_cmdout)
            bootapp.updateinfo("Connecting to databases")
            bootapp.updatesubinfo(f"Connecting to Local DB")
            bootapp.update()  # Force an update of the GUI

            try:
                sqdb = database.sqlite()
                sqdb.connect("configs/database.db")
                if cfg['init_db']:
                    sqdb.create_table(table="settings", values="id INT, itemkey VARCHAR, value VARCHAR")
                    exists = sqdb.fetchall(table='settings')
                    if not len(exists):
                        log.info(msg="Initializing settings", cmdout=info_cmdout)
                        sqdb.insertmultiple('settings', collumns='id, itemkey, value', values=['0, "appearance", "System"',
                                                                                               '1, "scaling", "100"',
                                                                                               '2, "fork", "base"',
                                                                                               '3, "version", "Latest"',
                                                                                               '4, "game_dir", "dir/"'])
                    #last_connected_exists = sqdb.insert_if_not_exists(table='user_data', filters='key=last_time_connected', collumns='key,value', values=("last_time_connected",datetime.datetime.now()))
                    if logging:
                        log.warn(msg='Tables were created. Please disable this in the config if this is not the first boot.')
                if logging:
                    log.info(msg='Database connected.', cmdout=info_cmdout)
            except Exception as e:
                boot_error = True
                critical = True
                msg = "An error occurred with Sqlite"
                err = e
        if not boot_error:
            log.info(msg='Downloading modlists...', cmdout=info_cmdout)
            r = requests.get(f"{cfg['user_preferences']['download_url']}/forks.yml",
                             allow_redirects=True)
            if r.status_code == 200:
                if os.path.exists('configs/forks.yml'):
                    os.remove('configs/forks.yml')
                open('configs/forks.yml', 'wb').write(r.content)
                fork = sqdb.fetchone(table='settings', filters='itemkey="fork"')
                with open(r'configs/forks.yml') as forklist:
                    forks = yaml.load(forklist, Loader=yaml.FullLoader)
            else:
                boot_error = True
                critical = True
                msg = "Connection to the mod server failed. Please check your internet connection or contact an admin"
                err = "no_200_response"
        if not boot_error:
            request = requests.get(f"{cfg['user_preferences']['download_url']}/{forks[fork[2]]['dir']}/info.yml",
                             allow_redirects=True)
            if request.status_code == 200:
                if os.path.exists('configs/info.yml'):
                    os.remove('configs/info.yml')
                open('configs/info.yml', 'wb').write(request.content)
                log.info(msg='Done downloading!', cmdout=info_cmdout)
            else:
                boot_error = True
                critical = True
                msg = "Connection to the mod server failed. Please check your internet connection or contact an admin"
                err = "no_200_response"




    if boot_error:
        bootapp.close_gui()
        if update:
            if logging:
                log.warn(msg=msg, err=err)
            error_app = ErrorGUI(msg=str(msg), err=str(err), time_wait=5, updater=True)
            error_app.after(5 * 1000,
                            launch_updater)  # Open the second GUI after a delay of 'timetowait' seconds (see param at top of if statement)
            error_app.mainloop()
            sys.exit()
        elif not critical:
            if logging:
                log.warn(msg=msg, err=err)
            error_app = ErrorGUI(msg=str(msg), err=str(err), time_wait=timetowait)
            error_app.after(timetowait * 1000,
                            open_second_gui)  # Open the second GUI after a delay of 'timetowait' seconds (see param at top of if statement)
            error_app.mainloop()
            sys.exit()
        else:
            if logging:
                log.error(msg=msg, err=err)
            error_app = ErrorGUI(msg=str(msg), err=str(err), time_wait=timetowait, critical=True)
            error_app.mainloop()
            sys.exit()

    else:
        log.info(msg='Launching main GUI', cmdout=info_cmdout)
        bootapp.close_gui()
        open_second_gui()
