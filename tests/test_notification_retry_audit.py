"""Repeated reconnects keep one subscription and bounded, cancellable retry."""
from unittest.mock import MagicMock
import pytest
from gns3.qt import QtNetwork
from gns3.project import Project

@pytest.mark.parametrize('scope',['controller','project'])
def test_reconnect_has_one_handler_and_a_deferred_retry(controller,scope):
    controller._connected=True
    controller._http_client.connectWebSocket.side_effect=lambda websocket,*args:websocket
    owner=controller if scope=='controller' else Project()
    for _ in range(8):
        owner._startListenNotifications()
        owner._websocket_error(QtNetwork.QAbstractSocket.SocketError.ConnectionRefusedError)
        assert owner._notification_retry.isActive()
        assert owner._notification_retry.interval()>=1000
        assert owner._websocket.receivers(owner._websocket.textMessageReceived)==1
    owner._event_received=MagicMock()
    owner._websocket.textMessageReceived.emit('{"action":"ping","event":{}}')
    owner._event_received.assert_called_once()
    owner.stopListenNotifications()
    assert not owner._notification_retry.isActive()
