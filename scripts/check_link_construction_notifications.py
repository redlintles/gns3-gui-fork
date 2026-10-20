#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check real server construction events using a disposable project.

Run with --server http://127.0.0.1:3099 against an isolated GNS3 2.2 server.
The transport, dispatcher and history are real; topology rendering is mocked.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from gns3.qt import QtWidgets, QtCore, QtWebSockets, QtNetwork
from gns3.project import Project
from gns3.history.model import HistoryDocument, state_from_lists


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True)
    args = parser.parse_args()
    app = QtWidgets.QApplication([])
    base = args.server.rstrip('/') + '/v2'
    def request(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(base + path, data=data, method=method,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as reply:
            raw = reply.read()
            return json.loads(raw) if raw else None
    def wait(condition):
        deadline = time.monotonic() + 5
        while not condition() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(.001)
        assert condition(), 'Timed out waiting for server events'
    project = request('POST', '/projects', {'name': 'Disposable link notification audit'})
    root = '/projects/' + project['project_id']
    socket = QtWebSockets.QWebSocket()
    try:
        nodes = [request('POST', root + '/nodes', dict(name=name, node_type='ethernet_switch', compute_id='local'))
                 for name in ('Audit1', 'Audit2')]
        owner = Project()
        owner.setId(project['project_id'])
        owner.history.document = HistoryDocument(owner.id(), state_from_lists({'nodes': nodes}))
        owner.history.ready = True
        # Avoid project-file uploads: this probe targets notification ordering.
        owner.history.persist = lambda: None
        events, errors = [], []
        owner.history.failed.connect(errors.append)
        def event(text):
            payload = json.loads(text)
            events.append(payload)
            owner._websocket_event_received(text)
        socket.textMessageReceived.connect(event)
        socket.open(QtCore.QUrl(args.server.replace('http://', 'ws://').replace('https://', 'wss://').rstrip('/') + '/v2' + root + '/notifications/ws'))
        wait(lambda: socket.state() == QtNetwork.QAbstractSocket.SocketState.ConnectedState)
        payload = {'nodes': [dict(node_id=n['node_id'], adapter_number=0, port_number=0) for n in nodes],
                   'link_style': {'color': '#123456', 'width': 3, 'type': 1}}
        with patch('gns3.project.Topology'):
            owner.history.begin()
            response = request('POST', root + '/links', payload)
            owner.history.observe('links', response)
            wait(lambda: any(e.get('action') == 'link.created' for e in events))
            owner.history.end()
            wait(lambda: owner.history.active is None)
        early = [e for e in events if e.get('action') == 'link.updated' and len(e['event'].get('nodes', [])) < 2]
        assert early, 'Server did not emit the construction notification expected by this probe'
        assert not errors, errors
        assert len(owner.history.document.entries) == 1
        assert len(owner.history.document.state['links/' + response['link_id']]['nodes']) == 2
        print(json.dumps({'transitional_events': early, 'history_entries': len(owner.history.document.entries),
                          'history_invalid': owner.history.invalid}, indent=2))
        print('PASS: transitional server event ignored; complete link recorded once')
    finally:
        socket.close()
        request('DELETE', root)


if __name__ == '__main__':
    main()
