import os.path
import datetime

import yaml

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
        with open(r'configs/config.yml') as config:
            self.cfg = yaml.load(config, Loader=yaml.FullLoader)
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

    def info(self, name:str=None, msg:str='No Message', cmdout=False):
        if name is None:
            name = self.defaultlog
        with open(self.cache['info', name], 'a') as file:
            file.write(f"{self._get_time_now()} [INFO]  {msg}\n")
        if cmdout:
            print(f"{self._get_time_now()} [{name}][INFO]  {msg}")

    def warn(self, name:str=None, msg:str='No Message', err=False, cmdout=True):
        errmsg = ''
        if name is None:
            name = self.defaultlog
        if err:
            errmsg = f"\n{self._get_time_now()} [ERMSG] {err}"
        with open(self.cache['info', name], 'a') as file:
            file.write(f"{self._get_time_now()} [WARN]  {msg}{errmsg}\n")
        if cmdout:
            print(f"{self._get_time_now()} [{name}][WARN]  {msg}{errmsg}")

    def error(self, name:str=None, msg:str='No Message', err:str='No Error', cmdout=True):
        if name is None:
            name = self.defaultlog
        with open(self.cache['error', name], 'a') as file:
            file.write(f"{self._get_time_now()} [ERROR] {msg}\n{self._get_time_now()} [{name}][ERMSG] {err}\n")
        if cmdout:
            print(f"{self._get_time_now()} [{name}][ERROR] {msg}\n{self._get_time_now()} [{name}][ERMSG] {err}")

    def _get_time_now(self, filename=False):
        if filename:
            return datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        else:
            return datetime.datetime.now().strftime('%d-%m-%Y | %H:%M:%S')

    def testdef(self, name:str):
        return self.cache.getitem(name)