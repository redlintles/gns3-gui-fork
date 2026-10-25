#!/usr/bin/env python3
"""Run exploratory families in fresh processes; nonzero exits preserve findings.
No production code is patched. Use a disposable server only for the separate
probe_server_geometry.py integration check.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'exploration'/'run-latest'
out.mkdir(parents=True,exist_ok=True)
config=Path(tempfile.mkdtemp(prefix='gns3-exploratory-config-'))
(config/'GNS3'/'2.2').mkdir(parents=True)
env={**os.environ,'QT_QPA_PLATFORM':os.environ.get('QT_QPA_PLATFORM','offscreen'),
     'XDG_CONFIG_HOME':str(config),'XDG_DATA_HOME':str(config/'data'),
     'GNS3_EXPLORATION_OUT':str(out)}
item='tests/items/probe_exploratory_sequences.py'
checks=[('tool-switch',item,'tool_switch_draws_wrong_kind'),
        ('generated-geometry',item,'generated_hierarchy or serialized_line'),
        ('shape-resize',item,'shape_resize_probe'),
        ('alpha-roundtrip',item,'generated_alpha'),
        ('image-ratio',item,'image_ratio'),
        ('image-interrupted',item,'image_interrupted'),
        ('generated-history','tests/history/probe_exploratory_sequences.py','generated_history_oracle')]
results=[]
for name,module,selection in checks:
    cmd=[sys.executable,'-m','pytest','-q',module,'-k',selection]
    with (out/(name+'.log')).open('w') as log:
        try:
            r=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=45)
            result={'name':name,'command':cmd,'returncode':r.returncode}
        except subprocess.TimeoutExpired:
            result={'name':name,'command':cmd,'timeout':True}
    results.append(result)
    print(result,flush=True)
(out/'manifest.json').write_text(json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
    'platform':sys.platform,'qt_platform':env['QT_QPA_PLATFORM'],'results':results},indent=2))
