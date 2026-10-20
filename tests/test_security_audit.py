"""Inert payloads: subprocesses intercepted; archive markers stay in tmp_path."""
import io
import json
import tarfile
from pathlib import Path
from unittest.mock import MagicMock,patch
from gns3.update_manager import UpdateManager
from gns3.telnet_console import ConsoleThread


def test_update_archive_cannot_escape_into_sibling(tmp_path):
    target=tmp_path/'site-packages';target.mkdir()
    sibling=tmp_path/'site-packages-audit';sibling.mkdir()
    archive=tmp_path/'audit.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        root=tarfile.TarInfo('package');root.type=tarfile.DIRTYPE;tar.addfile(root)
        member=tarfile.TarInfo('package/../site-packages-audit/marker.txt');data=b'INERT AUDIT MARKER';member.size=len(data);tar.addfile(member,io.BytesIO(data))
    manager=UpdateManager();manager._package_directory=str(target)
    try:manager._extractTgz(str(archive))
    except (ValueError,tarfile.TarError):pass
    assert not (sibling/'marker.txt').exists()


def test_console_title_is_one_argument(main_window,controller):
    node=MagicMock();node.name.return_value='audit-title extra-argument';node.consoleHost.return_value='127.0.0.1'
    node.project().name.return_value='Audit project'
    node.project().id.return_value='00000000-0000-0000-0000-000000000001'
    thread=ConsoleThread(None,'kitty -T {name} telnet {host} {port}',node,5000)
    with patch('gns3.telnet_console.subprocess.Popen') as popen,patch('gns3.telnet_console.shutil.which',return_value=None):
        thread.run()
    args=popen.call_args.args[0]
    assert args[2]==node.name(),args

import os
import sys
import pytest
from gns3.utils.console_command import console_command,split_command

@pytest.mark.parametrize('name', ['Router "quoted"', 'Router; literal', 'Router$(AUDIT)', 'Router {port} %h', 'Roteador São Paulo'])
def test_unix_console_values_are_literal_arguments(name):
    args=console_command('terminal -T "{name}" -- telnet {host} {port}',dict(name=name,host='::1',port=5000))
    assert args==['terminal','-T',name,'--','telnet','::1','5000']

@pytest.mark.parametrize('template', ['{name} {host}', 'sh -c "{name}"', 'osascript -e "{name}"'])
def test_project_data_cannot_choose_an_interpreter_program(template):
    with pytest.raises(ValueError):console_command(template,dict(name='AUDIT',host='localhost',port=5000))

@pytest.mark.parametrize('host', ['localhost;AUDIT', 'localhost extra', '$(AUDIT)', '%COMSPEC%'])
def test_console_host_rejects_command_syntax(host):
    with pytest.raises(ValueError):console_command('terminal {host} {port}',dict(host=host,port=5000))

@pytest.mark.skipif(not sys.platform.startswith('win'),reason='Native Windows quoting API')
def test_windows_native_quoting_keeps_path_and_title():
    assert split_command(r'"C:\Program Files\Client\terminal.exe" -T "Router one"')==[r'C:\Program Files\Client\terminal.exe','-T','Router one']

@pytest.mark.parametrize('kind',['symlink','hardlink'])
def test_update_archive_rejects_links(tmp_path,kind):
    target=tmp_path/'site-packages';target.mkdir();outside=tmp_path/'outside';outside.mkdir()
    archive=tmp_path/'links.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        root=tarfile.TarInfo('package');root.type=tarfile.DIRTYPE;tar.addfile(root)
        link=tarfile.TarInfo('package/link');link.type=tarfile.SYMTYPE if kind=='symlink' else tarfile.LNKTYPE;link.linkname=str(outside);tar.addfile(link)
    manager=UpdateManager();manager._package_directory=str(target)
    with pytest.raises(ValueError):manager._extractTgz(str(archive))
    assert not (target/'link').exists()


def test_applescript_title_is_escaped_after_template_parsing():
    template = r'''osascript -e 'do script "echo -n -e \"\\033]0;{name}\\007\"; telnet {host} {port}"' '''
    args=console_command(template,dict(name='Router$(AUDIT) "quote" \'apostrophe',host='localhost',port=5000))
    assert len(args)==3
    assert '\\\\$' in args[2]
    assert '\\\\\\"quote' in args[2]
    assert "'apostrophe" in args[2]


def test_unsafe_archive_is_rejected_before_any_package_file_changes(tmp_path):
    target=tmp_path/'site-packages';target.mkdir();existing=target/'preserved.txt';existing.write_text('original')
    archive=tmp_path/'atomic-validation.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        root=tarfile.TarInfo('package');root.type=tarfile.DIRTYPE;tar.addfile(root)
        for name in ['package/preserved.txt','package/../outside.txt']:
            item=tarfile.TarInfo(name);item.size=6;tar.addfile(item,io.BytesIO(b'MARKER'))
    manager=UpdateManager();manager._package_directory=str(target)
    with pytest.raises(ValueError):manager._extractTgz(str(archive))
    assert existing.read_text()=='original'
