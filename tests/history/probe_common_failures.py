"""Fault schedules and semantic invariants; production code is unchanged."""
import copy
import json
from pathlib import Path
from unittest.mock import MagicMock
from .test_session import session,ReallocatingServer,FileServer,edit,settled
from .test_model_replay import node,link,drawing,key
from gns3.history.model import canonical

OUT=Path(__file__).resolve().parents[2]/'exploration'/'common'
OUT.mkdir(parents=True,exist_ok=True)

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

def test_reversed_acknowledgments_preserve_last_server_state():
    a=node('A');owner,h,server=session(FileServer({key('nodes',a):a}));queued=[]
    h.begin('One operation with two confirmed writes')
    for x in [10,20]:
        cb=h.capture('PUT','/'+key('nodes',a),None,{'x':x})
        server.request('PUT','/'+key('nodes',a),lambda result,cb=cb:queued.append((cb,copy.deepcopy(result))),{'x':x})
    # Both requests reached the server in order, but their responses arrive backwards.
    for cb,result in reversed(queued):cb(result)
    h.end();settled(h)
    observed={'server_x':server.state[key('nodes',a)]['x'],'history_x':h.document.state[key('nodes',a)]['x'],'invalid':h.invalid}
    (OUT/'reversed-ack.json').write_text(json.dumps(observed,indent=2))
    assert observed['server_x']==observed['history_x'],observed
