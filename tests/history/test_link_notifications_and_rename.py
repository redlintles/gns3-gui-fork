"""Server construction notifications must not enter GUI/history as complete links."""
import json
from unittest.mock import MagicMock, patch
import pytest
from gns3.project import Project
from gns3.history.model import canonical, HistoryDocument
from .test_model_replay import node, link, delta, identity
from .test_session import session, FileServer, edit, settled


@pytest.mark.parametrize('count', [0, 1])
def test_transient_link_update_does_not_touch_history_or_gui(count):
    a, b = node('A'), node('B')
    data = link(a, b)
    data['nodes'] = data['nodes'][:count]
    owner = MagicMock()
    # Run the real event dispatcher, including JSON websocket decoding.
    owner._event_received.side_effect = lambda event: Project._event_received(owner, event)
    with patch('gns3.project.Topology') as topology:
        Project._websocket_event_received(owner, json.dumps({'action': 'link.updated', 'event': data}))
    owner.history.observe.assert_not_called()
    topology.instance.assert_not_called()
    # Persistence and API acknowledgments must still reject incomplete links.
    with pytest.raises(ValueError, match='two endpoints'):
        canonical('links', data)


def test_complete_link_event_and_partial_style_update_still_reach_gui():
    data = link(node('A'), node('B'))
    owner = MagicMock()
    owner.history.replaying = False
    with patch('gns3.project.Topology') as topology:
        Project._event_received(owner, {'action': 'link.created', 'event': data})
        partial = {'link_id': data['link_id'], 'link_style': {'width': 3}}
        Project._event_received(owner, {'action': 'link.updated', 'event': partial})
        topology.instance().getLinkFromUuid.return_value.updateLinkCallback.assert_called_once_with(partial)
    assert owner.history.observe.call_count == 2


@pytest.mark.parametrize('hint', [None, 'Change device properties'])
def test_rename_description_overrides_generic_hint_and_roundtrips(hint):
    before = node('Router1')
    after = dict(before, name='Router2', label={'text': 'Router2'})
    doc = HistoryDocument(identity('project'))
    doc.record(delta('nodes', before, after), hint)
    assert doc.entries[-1]['description'] == 'Changed Router1 hostname to Router2'
    from gns3.history.storage import encode, decode
    path = encode(doc.payload())
    try:
        loaded = decode(path.read_bytes())
    finally:
        path.unlink()
    assert loaded.entries[-1]['description'] == doc.entries[-1]['description']


def test_other_properties_retain_generic_description():
    before = node('Router1')
    after = dict(before, properties={'ram': 512})
    doc = HistoryDocument(identity('project'))
    doc.record(delta('nodes', before, after), 'Change device properties')
    assert doc.entries[-1]['description'] == 'Change device properties'


def test_rename_undo_redo_preserves_identity():
    before = node('Router1')
    key = 'nodes/' + before['node_id']
    owner, history, server = session(FileServer({key: before}))
    history.begin('Change device properties')
    edit(history, server, 'PUT', '/' + key, {'name': 'Router2'})
    history.end()
    settled(history)
    assert history.document.entries[-1]['description'] == 'Changed Router1 hostname to Router2'
    assert history.navigate(0)
    settled(history)
    assert server.state[key]['name'] == 'Router1'
    assert history.navigate(1)
    settled(history)
    assert server.state[key]['name'] == 'Router2'
    assert server.state[key]['node_id'] == before['node_id']
