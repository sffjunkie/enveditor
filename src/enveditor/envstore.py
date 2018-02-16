from collections import defaultdict
from enum import Enum
from collections import namedtuple
import os
import pprint
import re
import winreg

class EnvLocation(Enum):
    ENV_SYSTEM = 1
    ENV_USER = 2
    ENV_BOTH = 3


EnvKey = namedtuple('EnvKey', ['value', 'type', 'expanded'])


class Env():
    """The Environemt which contains the system and user variables"""

    def __init__(self):
        self.system = {}
        self.user = {}

    def shared_variables(self):
        """Returns a list of the environment variables that are common between system and user."""

        for system_key in self.system:
            if system_key in self.user:
                yield system_key

    def get(self, key, location=EnvLocation.ENV_BOTH, exact=True):
        """Return environment variables which contain `key`"""

        result = defaultdict(dict)

        if location == EnvLocation.ENV_SYSTEM or location == EnvLocation.ENV_BOTH:
            for env_key, value in self.system.items():
                if value[1] == 2:
                    expanded = self._expand(value[0])
                else:
                    expanded = None
                if (not exact and key in env_key) or (exact and key == env_key):
                    result[env_key]['system'] = EnvKey(value[0], value[1], expanded)

        if location == EnvLocation.ENV_USER or location == EnvLocation.ENV_BOTH:
            for env_key, value in self.user.items():
                if value[1] == 2:
                    expanded = self._expand(value[0])
                else:
                    expanded = None
                if (not exact and key in env_key) or (exact and key == env_key):
                    result[env_key]['user'] = EnvKey(value[0], value[1], expanded)

        return result

    def _expand(self, value):
        rc = re.compile(r'%(\w+)%')
        if not isinstance(value, list):
            value = [value]

        expanded = []
        for elem in value:
            for match in rc.finditer(elem):
                env_key = match.group(0)[1:-1]
                env_value = os.environ.get(env_key, '')
                elem = elem.replace('%%%s%%' % env_key, env_value)
            expanded.append(elem)

        if len(expanded) == 1:
            return expanded[0]
        else:
            return expanded


class WindowsEnvStore():
    def __init__(self):
        """Use the Windows Registry to extract environment variables"""
        self.env = None
        self._location_system = (winreg.HKEY_LOCAL_MACHINE,
                                 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment')
        self._location_user = (winreg.HKEY_CURRENT_USER,
                               'Environment')

    def _subkeys(self, key):
        key = winreg.OpenKey(key[0], key[1])
        info = winreg.QueryInfoKey(key)
        for idx in range(info[1]):
            k = winreg.EnumValue(key, idx)
            yield k

    def update(self):
        """Update the environment variables from the Windows Registry"""
        self.env = Env()
        for subkey in self._subkeys(self._location_system):
            if os.pathsep in subkey[1]:
                value = subkey[1].split(os.pathsep)
            else:
                value = subkey[1]

            self.env.system[str(subkey[0]).lower()] = value, subkey[2]

        for subkey in self._subkeys(self._location_user):
            if os.pathsep in subkey[1]:
                value = subkey[1].split(os.pathsep)
            else:
                value = subkey[1]

            self.env.user[str(subkey[0]).lower()] = value, subkey[2]
