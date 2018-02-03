import winreg

class Env():
    """The Environemt which contains the system and user variables"""

    def __init__(self):
        self.system = {}
        self.user = {}


class WindowsEnvStore():
    def __init__(self):
        """Use the Windows Registry to extract environment variables"""

        self._location_system = (winreg.HKEY_LOCAL_MACHINE,
                                 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment')
        self._location_user = (winreg.HKEY_CURRENT_USER,
                               'Environment')
        self.env = Env()

    def _subkeys(self, key):
        key = winreg.OpenKey(key[0], key[1])
        info = winreg.QueryInfoKey(key)
        for idx in range(info[1]):
            k = winreg.EnumValue(key, idx)
            yield k

    def load(self):
        """Load the environment variables from the Windows Registry"""

        for subkey in self._subkeys(self._location_system):
            self.env.system[str(subkey[0]).lower()] = subkey[1], subkey[2]

        for subkey in self._subkeys(self._location_user):
            self.env.user[str(subkey[0]).lower()] = subkey[1], subkey[2]
