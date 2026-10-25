"""Delayed callbacks and painting/geometry bookkeeping probes."""
import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock
from PyQt6.QtTest import QTest
from gns3.qt import QtCore,sip
from test_group_item import canvas,drawing,group

OUT=Path(__file__).resolve().parents[2]/'exploration'/'common'
OUT.mkdir(parents=True,exist_ok=True)

def test_drawing_ack_after_scene_clear_is_ignored(canvas):
    project=MagicMock();canvas._topology.project.return_value=project
    item=canvas.createDrawingItem('rect',100,100,0,drawing_id=str(uuid.uuid4()),create=False)
    item.updateDrawing()
    callback=project.put.call_args.args[1]
    payload=dict(item.__json__(),svg=item.toSvg())
    canvas.scene().clear()
    assert sip.isdeleted(item)
    try:callback(payload)
    except Exception as error:
        (OUT/'deleted-callback.json').write_text(json.dumps({'exception':type(error).__name__,'message':str(error),'cpp_deleted':sip.isdeleted(item)},indent=2))
        raise

def test_container_restore_pending_flag_finishes_after_project_change(canvas):
    # A restore scheduled on one project must not mutate the next project.
    a,b=object(),object();canvas._topology.project.return_value=a
    canvas._groups.scheduleRestore()
    canvas._topology.project.return_value=b
    QTest.qWait(30)
    assert not canvas._groups._restore_pending

def test_valid_fractional_svg_does_not_abort_project_loading(canvas):
    from gns3.project import Project
    from gns3.topology import Topology
    topo=Topology.instance();old=(topo._main_window,topo._project,topo._drawings,canvas._topology)
    p=Project();p.setId(str(uuid.uuid4()));topo._main_window=canvas._main_window;topo._project=p;topo._drawings=[];canvas._topology=topo
    payload={'drawing_id':str(uuid.uuid4()),'x':0,'y':0,'z':0,'locked':False,'rotation':0,
             'svg':'<svg width="100" height="50"><line x1="0" y1="0" x2="100" y2="50" stroke="#123456" stroke-width="2.5"/></svg>'}
    caught=None
    try:
        try:p._listDrawingsCallback([payload])
        except Exception as error:caught={'type':type(error).__name__,'message':str(error)}
        (OUT/'fractional-svg-load.json').write_text(json.dumps({'exception':caught,'history_ready':p.history.ready,'created_drawings':len(topo._drawings),'payload':payload},indent=2))
        assert caught is None,caught
    finally:topo._main_window,topo._project,topo._drawings,canvas._topology=old


def test_zoomed_visible_line_handle_resizes_instead_of_moving_body(canvas):
    from gns3.qt import QtGui
    canvas.window().resize(1100,800);canvas.window().show();canvas.resize(1000,700)
    canvas._main_window.uiShowGridAction.isChecked.return_value=False
    canvas.setSceneRect(-200,-200,500,400)
    line=canvas.createDrawingItem('line',0,0,0,create=False);line.setLine(0,0,60,0);line.setSelected(True)
    canvas.scale(5,5);canvas.centerOn(30,0);QTest.qWait(30)
    first=line.mapToScene(line.line().p1());second=line.mapToScene(line.line().p2())
    center=canvas.mapFromScene(second);click=center+QtCore.QPoint(12,0)
    assert canvas.viewport().rect().contains(click)
    # A 4-scene-unit handle paints 20px either side of its center at this zoom.
    assert abs(click.x()-center.x())<4*canvas.transform().m11()
    canvas.window().grab().save(str(OUT/'zoom-handle-before.png'))
    QTest.mousePress(canvas.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=click)
    mode='endpoint' if canvas._lines._resize is not None else 'body'
    QTest.mouseMove(canvas.viewport(),click+QtCore.QPoint(30,0))
    QTest.mouseRelease(canvas.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=click+QtCore.QPoint(30,0))
    after_first=line.mapToScene(line.line().p1());after_second=line.mapToScene(line.line().p2())
    observed={'zoom':5,'click_offset_px':12,'painted_handle_halfwidth_px':20,'mode':mode,
              'first_before':[first.x(),first.y()],'first_after':[after_first.x(),after_first.y()],
              'second_before':[second.x(),second.y()],'second_after':[after_second.x(),after_second.y()]}
    (OUT/'zoom-handle.json').write_text(json.dumps(observed,indent=2))
    canvas.window().grab().save(str(OUT/'zoom-handle-after.png'))
    assert QtCore.QLineF(first,after_first).length()<.001,observed
