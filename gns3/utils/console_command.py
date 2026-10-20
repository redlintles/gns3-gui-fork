# SPDX-License-Identifier: GPL-3.0-or-later
"""Expand untrusted console labels only after parsing the trusted template."""
import re
import shlex
import sys


def split_command(command):
    if not sys.platform.startswith('win'):
        return shlex.split(command)
    # Use Windows' native quoting rules, not POSIX shlex (which eats path '\\').
    import ctypes
    from ctypes import wintypes
    parser = ctypes.windll.shell32.CommandLineToArgvW
    parser.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    parser.restype = ctypes.POINTER(wintypes.LPWSTR)
    count = ctypes.c_int()
    pointer = parser(command.strip(), ctypes.byref(count))
    if not pointer:
        raise ValueError('Invalid console command')
    try:
        return [pointer[i] for i in range(count.value)]
    finally:
        free = ctypes.windll.kernel32.LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        free(ctypes.cast(pointer, ctypes.c_void_p))


def _applescript_title(value):
    # Presets embed a double-quoted shell title inside an AppleScript string.
    # Protect BOTH interpreters. Values never pass through shlex afterwards.
    shell = ''.join('\\' + c if c in '\\$`"' else c for c in value)
    return shell.replace('\\', '\\\\').replace('"', '\\"')


def console_command(command, values):
    aliases = {'h':'host', 'p':'port', 'd':'name', 'P':'project', 'i':'project_id',
               'n':'node_id', 'c':'url', 'D':'display'}
    values = {key: str(value) for key, value in values.items()}
    host = values.get('host', '')
    if host and (not re.fullmatch(r'[\w.:%\[\]-]+', host) or ('%' in host and ':' not in host)):
        raise ValueError('Invalid console host')
    if any(any(ord(c) < 32 or ord(c) == 127 for c in value) for value in values.values()):
        raise ValueError('Control characters are not allowed in console parameters')
    args = split_command(command)
    if not args:
        raise ValueError('Console command is empty')
    executable = args[0].replace('\\', '/').rsplit('/', 1)[-1].lower()
    apple = executable == 'osascript'
    pattern = re.compile(r'\{(' + '|'.join(map(re.escape, values)) + r')\}|%([hpdPincD])')
    if pattern.search(args[0]):
        raise ValueError('Console executable must not come from project data')
    if 'port' in values and (not values['port'].isascii() or not values['port'].isdecimal() or
                             not 1 <= int(values['port']) <= 65535):
        raise ValueError('Invalid console port')
    for index, token in enumerate(args[1:], 1):
        if executable in ('sh', 'bash', 'zsh', 'cmd', 'cmd.exe', 'powershell', 'powershell.exe', 'pwsh'):
            if args[index - 1].lower() in ('-c', '/c', '-command', '-encodedcommand') and pattern.search(token):
                raise ValueError('Pass console parameters as separate arguments, not interpreter code')
        if apple and args[index - 1] == '-e':
            labels = [m.group(1) or aliases[m.group(2)] for m in pattern.finditer(token)]
            if any(key in ('name', 'project') for key in labels) and not ('echo -n -e' in token and ']0;' in token and '007' in token):
                raise ValueError('Use console labels only in the supported AppleScript title preset')
    def expand(token, script):
        def substitute(match):
            key = match.group(1) or aliases[match.group(2)]
            value = values.get(key, match.group())
            return _applescript_title(value) if script and key in ('name', 'project') else value
        return pattern.sub(substitute, token)
    return [expand(token, apple and index > 0 and args[index - 1] == '-e') for index, token in enumerate(args)]
