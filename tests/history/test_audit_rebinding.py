"""Fault schedules and semantic invariants; production code is unchanged."""
import copy
import json
from pathlib import Path
from unittest.mock import MagicMock
from .test_session import session,ReallocatingServer,FileServer,edit,settled
from .test_model_replay import node,link,drawing,key
from gns3.history.model import canonical

import pytest
@pytest.fixture(autouse=True)
def evidence(tmp_path):
    global OUT
    OUT=tmp_path

def test_link_id_rebinding_does_not_rewrite_note_text():
    a,b=node('A'),node('B');connection=link(a,b)
    note=drawing('annotation');note['svg']='<svg width="500" height="30"><text>Reference '+connection['link_id']+'</text></svg>'
    owner,h,server=session(ReallocatingServer({key('nodes',a):a,key('nodes',b):b,key('links',connection):connection,key('drawings',note):note}))
    owner._event_received=MagicMock()
    edit(h,server,'DELETE','/'+key('links',connection));settled(h)
    assert h.navigate(0);settled(h)
    observed={'old_link_id':connection['link_id'],'new_link_id':next(v['link_id'] for k,v in server.state.items() if k.startswith('links/')),
              'server_svg':server.state[key('drawings',note)]['svg'],'history_svg':h.document.state[key('drawings',note)]['svg'],'invalid':h.invalid}
    try:h.document.remap_import(owner.id(),{k:canonical(k.split('/')[0],v) for k,v in server.state.items()})
    except ValueError as e:observed['reopen_validation_error']=str(e)
    (OUT/'rebind-user-text.json').write_text(json.dumps(observed,indent=2))
    assert observed['history_svg']==observed['server_svg'],observed
