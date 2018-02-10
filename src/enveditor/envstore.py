from collections import defaultdict
from enum import Enum
from pprint import pprint
import os
import winreg

class EnvLocation(Enum):
    ENV_SYSTEM = 1
    ENV_USER = 2
    ENV_BOTH = 3


class Env():
    """The Environemt which contains the system and user variables"""

    def __init__(self):
        self.system = {}
        self.user = {}

    def shared_keys(self):
        """Returns a list of the keys that are common between the system and user variables"""

        for system_key in self.system:
            if system_key in self.user:
                yield system_key

    def get(self, key, location=EnvLocation.ENV_BOTH, exact=True):
        """Return environment variables which contain `key`"""

        result = defaultdict(dict)

        if location == EnvLocation.ENV_SYSTEM or location == EnvLocation.ENV_BOTH:
            for env_key, value in self.system.items():
                if (not exact and key in env_key) or (exact and key == env_key):
                    result['system'][env_key] = value

        if location == EnvLocation.ENV_USER or location == EnvLocation.ENV_BOTH:
            for env_key, value in self.user.items():
                if (not exact and key in env_key) or (exact and key == env_key):
                    result['user'][env_key] = value

        return result


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
            if os.pathsep in subkey[1]:
                value = subkey[1].split(os.pathsep)
            else:
                value = subkey[1]

            type_ = subkey[2]

            self.env.system[str(subkey[0]).lower()] = value, type_

        for subkey in self._subkeys(self._location_user):
            if os.pathsep in subkey[1]:
                value = subkey[1].split(os.pathsep)
            else:
                value = subkey[1]

            type_ = subkey[2]

            self.env.user[str(subkey[0]).lower()] = value, type_
