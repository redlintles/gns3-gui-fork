#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify GUI history against a disposable GNS3 2.2 server (never a personal project).

Uses the actual Qt HTTP client, Project, node/link models and canvas. Creates and
removes its own projects; no emulator/image is needed for Ethernet switches.
"""
import argparse
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.request
import uuid
import zipfile
from unittest.mock import patch
from urllib.parse import urlparse
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from gns3.qt import QtWidgets, QtCore, QtGui
from gns3.local_config import LocalConfig
from gns3.main_window import MainWindow
from gns3.topology import Topology
from gns3.controller import Controller
from gns3.project import Project
from gns3.http_client import HTTPClient
from gns3.history.storage import SLOTS
from gns3.items.group_item import GroupItem
from gns3.items.rectangle_item import RectangleItem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True)
    args = parser.parse_args()
    app = QtWidgets.QApplication([])
    directory = Path(tempfile.mkdtemp(prefix='gns3-history-check-'))
    LocalConfig._instance = LocalConfig(config_file=str(directory / 'gui.json'))
    url = urlparse(args.server)
    base = args.server.rstrip('/') + '/v2'
    def request(method, path, body=None, raw=False):
        data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(base + path, data=data, method=method,
            headers={'Content-Type': 'application/octet-stream' if isinstance(body, bytes) else 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            value = response.read()
        return value if raw else json.loads(value) if value else {}
    def wait(condition, timeout=15):
        start = time.monotonic()
        while not condition() and time.monotonic() - start < timeout:
            app.processEvents()
            time.sleep(.005)
        assert condition(), 'Timed out waiting for history/server synchronization'
    http = HTTPClient({'host': url.hostname, 'port': url.port or 80, 'protocol': url.scheme})
    http._connected = True
    controller = Controller.instance()
    controller._http_client = http
    controller._connected = True
    for name in ('XDG_CONFIG_HOME','XDG_DATA_HOME'):
        if os.environ.get(name):Path(os.environ[name],'GNS3','2.2').mkdir(parents=True,exist_ok=True)
    from gns3.local_server import LocalServer
    with patch.object(MainWindow, 'run_later'), patch.object(LocalServer, 'localServerAutoStartIfRequired'):
        window = MainWindow()
    controller._http_client = http
    controller._connected = True
    topo = Topology.instance()
    ids = []
    def attach(pid):
        project = Project()
        project.setId(pid)
        project.setName('History integration')
        project._created = True
        project._closed = False
        topo.setProject(project)
        controller._http_client = http
        controller._connected = True
        project._startListenNotifications()
        wait(lambda: project._websocket.isValid())
        return project
    def settled(history):
        wait(lambda: not history.busy and not history._saving)
        assert not history.invalid, history.invalid
    def edit(project, method, path, body=None):
        done = []
        getattr(project, method.lower())(path, lambda result, error=False, **kw: done.append((result, error)), body=body)
        wait(lambda: bool(done))
        assert not done[0][1], done[0][0]
        settled(project.history)
        return done[0][0]
    try:
        from PyQt6.QtTest import QTest
        out=Path(__file__).resolve().parent/'common';out.mkdir(exist_ok=True)
        pid=request('POST','/projects',{'name':'Disposable common bug rebinding'})['project_id'];ids.append(pid)
        project=attach(pid);history=project.history
        loaded=[];history.load({},lambda:loaded.append(True));wait(lambda:bool(loaded))
        HTTPClient.setProgressCallback(None)
        view=window.uiGraphicsView;window.resize(1100,850);window.show()
        a=edit(project,'POST','/nodes',dict(node_type='ethernet_switch',compute_id='local',name='A',x=0,y=0))
        b=edit(project,'POST','/nodes',dict(node_type='ethernet_switch',compute_id='local',name='B',x=200,y=0))
        for data in [a,b]:
            if topo.getNodeFromUuid(data['node_id']) is None:topo.createNode(data)
        connection=edit(project,'POST','/links',{'nodes':[dict(node_id=a['node_id'],adapter_number=0,port_number=0),dict(node_id=b['node_id'],adapter_number=0,port_number=0)]})
        note=view.createDrawingItem('text',0,180,2,create=False)
        original='Reference '+connection['link_id'];note.setPlainText(original);note.create();settled(history)
        note_id=note.drawing_id();before=history.document.cursor
        view.centerOn(100,100);QTest.qWait(100);window.grab().save(str(out/'rebind-before.png'))
        edit(project,'DELETE','/links/'+connection['link_id']);settled(history)
        assert history.navigate(before);settled(history)
        new_link=request('GET','/projects/'+pid+'/links')[0]['link_id']
        result={'old_id':connection['link_id'],'new_id':new_link,'original_text':original,'canvas_after_undo':note.toPlainText(),
            'server_svg':next(d['svg'] for d in request('GET','/projects/'+pid+'/drawings') if d['drawing_id']==note_id),
            'history_svg':history.document.state['drawings/'+note_id]['svg'],'history_invalid':history.invalid,'cursor_before_close':history.document.cursor}
        window.grab().save(str(out/'rebind-after-undo.png'))
        project.close();wait(lambda:project._closed and topo.project() is None)
        request('POST','/projects/'+pid+'/open');project=attach(pid);history=project.history
        project._listNodesCallback(request('GET','/projects/'+pid+'/nodes'));wait(lambda:history.ready);settled(history)
        note=topo.getDrawingFromUuid(note_id)
        result.update(canvas_after_reopen=note.toPlainText(),cursor_after_reopen=history.document.cursor,recovery=history.recovery_message)
        (out/'rebind-real-server.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2),flush=True)
    except Exception:
        import traceback
        traceback.print_exc()
        raise
    finally:
        topo.setProject(None)
        window._local_config_timer.stop()
        http._shutdown = True
        window.deleteLater()
        app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        app.processEvents()
        for pid in reversed(ids):
            request('DELETE', '/projects/' + pid)


if __name__ == '__main__':
    main()
