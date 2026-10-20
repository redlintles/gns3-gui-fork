# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Functions to start SPICE console programs.
"""

import sys
import os
import shlex
import subprocess
from .utils.console_command import console_command, split_command

from .controller import Controller

import logging
log = logging.getLogger(__name__)


def spiceConsole(node, port, command):
    """
    Start a SPICE console program.

    :param node: Node instance
    :param port: port number
    :param command: command to be executed
    """

    if len(command.strip(' ')) == 0:
        log.error("SPICE client is not configured")
        return

    name = node.name()
    host = node.consoleHost()

    # ipv6 support
    if ":" in host:
        host = "[{}]".format(host)

    try:
        args = console_command(command, dict(host=host, port=port, display=int(port) - 5900, name=name,
            project=node.project().name(), project_id=node.project().id(), node_id=node.id(),
            url=Controller.instance().httpClient().fullUrl()))
    except ValueError as error:
        log.error('Invalid console parameters: %s', error)
        return

    try:
        log.debug('starting SPICE program "{}"'.format(command))
        if sys.platform.startswith("win"):
            # use the string on Windows
            subprocess.Popen(args, env=os.environ)
        else:
            # use arguments on other platforms
            subprocess.Popen(args, env=os.environ)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        log.error("Could not start SPICE program with command '{}': {}".format(command, e))
