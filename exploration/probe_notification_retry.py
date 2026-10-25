#!/usr/bin/env python3
"""Bounded connection-refusal experiment; no live project is opened."""
import json
import logging
import sys
import tempfile
import time
import uuid
from unittest.mock import MagicMock
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gns3.qt import QtCore,QtWidgets,QtNetwork
from PyQt6.QtTest import QTest
from gns3.local_config import LocalConfig
from gns3.controller import Controller
from gns3.http_client import HTTPClient
from gns3.project import Project
app=QtWidgets.QApplication([])
LocalConfig._instance=LocalConfig(config_file=str(Path(tempfile.mkdtemp())/'gui.json'))
# Reserve then release an ephemeral port, ensuring connection refusal rather than
# using any configured/personal GNS3 server.
probe=QtNetwork.QTcpServer();assert probe.listen(QtNetwork.QHostAddress('127.0.0.1'),0)
port=probe.serverPort();probe.close()
c=Controller.instance();c._http_client=HTTPClient({'host':'127.0.0.1','port':port,'protocol':'http'});c._connected=True
p=Project();p.setId(str(uuid.uuid4()))
start=time.monotonic();events=[]
error=p._websocket.error if tuple(map(int,QtCore.QT_VERSION_STR.split('.')[:2]))<(6,5) else p._websocket.errorOccurred
# Stop before this intentionally bounded experiment can amplify indefinitely.
def observed(*args):
    events.append({'ms':round((time.monotonic()-start)*1000,3),'error_handlers':p._websocket.receivers(error),'text_handlers':p._websocket.receivers(p._websocket.textMessageReceived)})
    if len(events)>=8:c._connected=False
error.connect(observed)
logging.disable(logging.CRITICAL)
p._startListenNotifications()
QTest.qWait(250)
c._connected=False
p._event_received=MagicMock()
p._websocket.textMessageReceived.emit('{"action":"ping","event":{}}')
dispatches=p._event_received.call_count
p.stopListenNotifications()
Path(__file__).resolve().parent.joinpath('common','notification-retry-'+QtCore.QT_VERSION_STR+'.json').write_text(json.dumps({'qt_build':QtCore.QT_VERSION_STR,'qt_runtime':QtCore.qVersion(),'pyqt':QtCore.PYQT_VERSION_STR,'events':events,'one_message_dispatches':dispatches},indent=2))
print(json.dumps(events),flush=True)
