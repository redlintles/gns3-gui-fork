"""Generated user-level history sequences with independent retained-state oracle."""
import copy
import json
import random
from pathlib import Path
import pytest
from .test_session import session,FileServer,edit,settled
from .test_model_replay import node,key
from gns3.history.model import canonical,HistoryDocument
from gns3.history.storage import encode,decode

@pytest.mark.parametrize('seed',range(12))
def test_generated_history_oracle(seed):
    rng=random.Random(seed); initial=node('A')
    owner,h,server=session(FileServer({key('nodes',initial):initial}))
    current=lambda:{k:canonical(k.split('/')[0],v) for k,v in server.state.items()}
    states=[copy.deepcopy(current())];cursor=0;trace=[]
    for step in range(310):
        op=rng.choice(['edit','edit','edit','undo','redo','navigate','reload','clear'])
        if step<130:op='edit'
        if op=='edit':
            h.begin('Generated move')
            count=rng.randint(1,4)
            x,y=rng.randint(-10000,10000),rng.randint(-10000,10000)
            for _ in range(count):edit(h,server,'PUT','/'+key('nodes',initial),{'x':x,'y':y})
            h.end();settled(h)
            actual=current()
            if actual!=states[cursor]:
                states=states[:cursor+1]+[copy.deepcopy(actual)]
                states=states[-101:];cursor=len(states)-1
        elif op in ['undo','redo','navigate']:
            target=max(0,cursor-1) if op=='undo' else min(len(states)-1,cursor+1) if op=='redo' else rng.randrange(len(states))
            assert h.navigate(target);settled(h);cursor=target
        elif op=='reload':
            path=encode(h.document.payload())
            try:h.document=decode(path.read_bytes())
            finally:path.unlink()
        elif op=='clear':
            h.clear();settled(h);states=[copy.deepcopy(current())];cursor=0
        trace.append(op)
        assert not h.invalid,(seed,step,trace,h.invalid)
        assert h.document.cursor==cursor,(seed,step,trace)
        assert h.document.state==states[cursor]==current(),(seed,step,trace)
    out=Path(__file__).resolve().parents[2]/'exploration'
    (out/('history-seed-%d.json'%seed)).write_text(json.dumps(trace))
