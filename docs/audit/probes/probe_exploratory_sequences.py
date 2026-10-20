"""Exploratory probes; production code intentionally unchanged."""
import json
import os
import random
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from PyQt6.QtTest import QTest
from gns3.qt import QtCore, QtGui, QtWidgets
from test_group_item import canvas, drawing, group
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
@pytest.fixture
def real_main_window():
    from gns3.main_window import MainWindow
    from gns3.controller import Controller
    from gns3.topology import Topology
    Controller._instance = None
    from gns3.local_server import LocalServer
    LocalServer._instance = None
    if hasattr(Topology,'_instance'):del Topology._instance
    import logging
    handlers=set(logging.getLogger().handlers)
    with patch.object(MainWindow,'run_later'), patch.object(LocalServer,'localServerAutoStartIfRequired'):
        w=MainWindow()
    yield w
    w._local_config_timer.stop()
    w.hide();w.deleteLater()
    for handler in set(logging.getLogger().handlers)-handlers:logging.getLogger().removeHandler(handler)


OUT = Path(os.environ.get('GNS3_EXPLORATION_OUT',str(Path(__file__).resolve().parents[2] / 'exploration')))
OUT.mkdir(parents=True,exist_ok=True)

def state(v):
    return {k: bool(getattr(v, '_adding_' + k)) for k in ['note','rectangle','ellipse','line','link']}

@pytest.mark.parametrize('first,second', [('Rectangle','Ellipse'),('Ellipse','Rectangle'),('Note','Rectangle'),('Rectangle','Note'),('Line','Rectangle'),('Rectangle','Line')])
def test_tool_switch_probe(real_main_window, first, second):
    w=real_main_window; v=w.uiGraphicsView
    w.resize(1000,800); w.show(); v.setEnabled(True); w.uiAnnotationToolBar.setEnabled(True)
    actions={'Rectangle':w.uiDrawRectangleAction,'Ellipse':w.uiDrawEllipseAction,'Note':w.uiAddNoteAction,'Line':w.uiDrawLineAction}
    actions[first].trigger(); actions[second].trigger()
    info={'sequence':[first,second], 'state':state(v), 'checked':{k:a.isChecked() for k,a in actions.items()}}
    (OUT / ('tool-'+first+'-'+second+'.json')).write_text(json.dumps(info,indent=2))
    w.grab().save(str(OUT / ('tool-'+first+'-'+second+'.png')))
    assert sum(state(v).values()) <= 1, info

@pytest.mark.parametrize('seed',range(25))
def test_generated_hierarchy_roundtrip(canvas,seed):
    rng=random.Random(seed); items=[drawing(canvas,kind=rng.choice(['rect','ellipse','text']),x=100*i,y=80) for i in range(5)]
    groups=[]; trace=[]
    from gns3.items.group_item import set_scene_position,read_group,reparent
    for step in range(60):
        op=rng.choice(['group','move','style','reload','detach'])
        roots=[i for i in items+groups if i.scene() is canvas.scene() and i.parentItem() is None]
        if op=='group' and len(roots)>1:
            chosen=rng.sample(roots,2); g=group(canvas,chosen); groups.append(g)
        elif op=='move' and roots:
            i=rng.choice(roots); set_scene_position(i,i.scenePos()+QtCore.QPointF(rng.randint(-100,100),rng.randint(-100,100)))
        elif op=='style' and groups:
            rng.choice(groups).setStyle({'shape':rng.choice(['rect','ellipse','triangle'])})
        elif op=='detach':
            children=[i for i in items+groups if i.parentItem() is not None]
            if children: reparent(rng.choice(children),None)
        elif op=='reload':
            canvas._groups.save(items+groups)
            before={i:(i.parentItem(),QtCore.QPointF(i.scenePos())) for i in items+groups}
            canvas._groups.restore(persist=False)
            for i,(parent,pos) in before.items():
                assert i.parentItem() is parent and QtCore.QLineF(pos,i.scenePos()).length()<1e-6,(seed,step,trace)
        trace.append(op)
        for i in items+groups:
            assert i.scene() is canvas.scene()
            assert i.isVisible()
            p=i.parentItem(); seen={i}
            while p:
                assert p not in seen;seen.add(p);p=p.parentItem()
    (OUT / ('hierarchy-seed-%d.json'%seed)).write_text(json.dumps(trace))

@pytest.mark.parametrize('nested',[False,True])
@pytest.mark.parametrize('locked',[False,True])
@pytest.mark.parametrize('edge',['top','left','right','bottom'])
def test_shape_resize_probe(canvas,nested,locked,edge):
    canvas.window().resize(900,700);canvas.window().show();canvas.resize(850,650)
    canvas.setSceneRect(-600,-500,1600,1300)
    canvas._main_window.uiShowGridAction.isChecked.return_value=False
    canvas.centerOn(200,150);QTest.qWait(20)
    shape=drawing(canvas,x=160,y=120)
    if nested:
        frame=group(canvas,[shape]);canvas._groups.enter(frame)
    shape.setSelected(True)
    if locked:canvas.lockActionSlot()
    canvas.centerOn(shape.sceneBoundingRect().center());QTest.qWait(20)
    old_rect=QtCore.QRectF(shape.rect()); old_pos=QtCore.QPointF(shape.scenePos())
    r=shape.rect(); point={'top':QtCore.QPointF(r.center().x(),1),'left':QtCore.QPointF(1,r.center().y()),'right':QtCore.QPointF(r.right()-1,r.center().y()),'bottom':QtCore.QPointF(r.center().x(),r.bottom()-1)}[edge]
    start=canvas.mapFromScene(shape.mapToScene(point)); delta=QtCore.QPoint(10,10)
    assert canvas.viewport().rect().contains(start)
    canvas.window().grab().save(str(OUT/('shape-%s-%s-%s-before.png'%(nested,locked,edge))))
    QTest.mousePress(canvas.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=start)
    QTest.mouseMove(canvas.viewport(),start+delta)
    QTest.mouseRelease(canvas.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=start+delta)
    info={'nested':nested,'locked':locked,'edge':edge,'before_rect': [old_rect.width(),old_rect.height()], 'after_rect':[shape.rect().width(),shape.rect().height()], 'before_pos':[old_pos.x(),old_pos.y()], 'after_pos':[shape.scenePos().x(),shape.scenePos().y()]}
    (OUT/('shape-%s-%s-%s.json'%(nested,locked,edge))).write_text(json.dumps(info,indent=2))
    canvas.window().grab().save(str(OUT/('shape-%s-%s-%s.png'%(nested,locked,edge))))
    if locked: assert shape.rect()==old_rect and shape.scenePos()==old_pos, info
    else:
        assert shape.rect().width()>0 and shape.rect().height()>0,info
        expected=old_rect.size()+QtCore.QSizeF(-10 if edge=='left' else 9 if edge=='right' else 0,-10 if edge=='top' else 9 if edge=='bottom' else 0)
        assert abs(shape.rect().width()-expected.width())<2 and abs(shape.rect().height()-expected.height())<2,info

@pytest.mark.parametrize('kind',['text','line','rect','ellipse'])
def test_generated_alpha_roundtrip(canvas,kind):
    from gns3.items.text_item import TextItem
    from gns3.items.line_item import LineItem
    failures=[]
    item=drawing(canvas,kind)
    for alpha in [0,1,2,8,15,16,64,128,255]:
        color=QtGui.QColor(18,52,86,alpha)
        if kind=='text':item.setDefaultTextColor(color)
        else:item.setPen(QtGui.QPen(color,4))
        svg=item.toSvg(); copy=type(item)(svg=svg)
        actual=copy.defaultTextColor() if kind=='text' else copy.pen().color()
        if actual.rgba()!=color.rgba(): failures.append({'alpha':alpha,'expected':color.name(QtGui.QColor.NameFormat.HexArgb),'actual':actual.name(QtGui.QColor.NameFormat.HexArgb),'svg':svg})
    (OUT/('alpha-'+kind+'.json')).write_text(json.dumps(failures,indent=2))
    assert not failures,failures

@pytest.mark.parametrize('width',[1,2,3,100,1000000])
def test_image_ratio_boundary(canvas,width):
    from gns3.dialogs.image_properties_dialog import ImagePropertiesDialog
    d=ImagePropertiesDialog(canvas,100,50)
    d.widthEdit.setValue(width)
    info={'width':d.widthEdit.value(),'height':d.heightEdit.value(),'keep':d.keepAspect.isChecked()}
    assert abs(d.widthEdit.value()/d.heightEdit.value()-2)<.02,info

def test_tool_switch_draws_wrong_kind(real_main_window):
    from gns3.items.rectangle_item import RectangleItem
    from gns3.items.ellipse_item import EllipseItem
    w=real_main_window;v=w.uiGraphicsView
    w.resize(1000,800);w.show();v.setEnabled(True);w.uiAnnotationToolBar.setEnabled(True)
    w.uiDrawRectangleAction.trigger();w.uiDrawEllipseAction.trigger()
    a,b=QtCore.QPoint(120,120),QtCore.QPoint(300,240)
    with patch('gns3.graphics_view.StyleEditorDialog.exec',return_value=QtWidgets.QDialog.DialogCode.Accepted):
        QTest.mousePress(v.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=a)
        QTest.mouseMove(v.viewport(),b)
        QTest.mouseRelease(v.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=b)
    made=[i for i in v.scene().items() if isinstance(i,(RectangleItem,EllipseItem))]
    (OUT/'tool-wrong-shape.json').write_text(json.dumps({'created':[type(i).__name__ for i in made], 'state':state(v)},indent=2))
    w.grab().save(str(OUT/'tool-wrong-shape.png'))
    assert len(made)==1 and isinstance(made[0],EllipseItem),[type(i).__name__ for i in made]

@pytest.mark.parametrize('seed',range(20))
def test_generated_serialized_line_geometry(canvas,seed):
    from gns3.items.line_item import LineItem
    from gns3.items.group_item import set_scene_position
    rng=random.Random(seed)
    line=canvas.createDrawingItem('line',0,0,0,create=False)
    line.setLine(-5,10,100,80)
    frame=group(canvas,[line]);canvas._groups.enter(frame)
    trace=[]
    for step in range(40):
        op=rng.choice(['move','rotate','end','save','restore'])
        if op=='move':set_scene_position(line,QtCore.QPointF(rng.uniform(-20,100),rng.uniform(-20,100)))
        elif op=='rotate':line.setRotation(rng.randint(0,359))
        elif op=='end':
            q=QtCore.QLineF(line.line());q.setP2(QtCore.QPointF(rng.uniform(-200,200),rng.uniform(-200,200)));line.setLine(q)
        before=[line.mapToScene(p) for p in (line.line().p1(),line.line().p2())]
        if op in ['save','restore']:
            payload=line.__json__();payload['svg']=line.toSvg()
            restored=LineItem(svg=payload['svg']);restored.setRotation(payload['rotation']);restored.setPos(payload['x'],payload['y'])
            after=[restored.mapToScene(p) for p in (restored.line().p1(),restored.line().p2())]
            assert all(QtCore.QLineF(a,b).length()<1e-6 for a,b in zip(before,after)),(seed,step,trace)
        trace.append(op)
    (OUT/('line-seed-%d.json'%seed)).write_text(json.dumps(trace))

def test_image_interrupted_resize_probe(canvas):
    from gns3.items.image_item import ImageItem
    canvas.window().resize(900,700);canvas.window().show();canvas.resize(850,650)
    canvas.setSceneRect(-600,-500,1600,1300)
    canvas._main_window.uiShowGridAction.isChecked.return_value=False
    bitmap=QtGui.QImage(100,50,QtGui.QImage.Format.Format_ARGB32);bitmap.fill(QtGui.QColor('green'))
    path=OUT/'image-fixture.png';bitmap.save(str(path))
    image=ImageItem(image_path=str(path),pos=QtCore.QPointF(0,0))
    canvas.scene().addItem(image);image.setSelected(True)
    canvas.centerOn(image.sceneBoundingRect().center());QTest.qWait(20)
    start=canvas.mapFromScene(image.mapToScene(image.boundingRect().bottomRight()-QtCore.QPointF(1,1)))
    QTest.mousePress(canvas.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=start)
    QTest.mouseMove(canvas.viewport(),start+QtCore.QPoint(50,25))
    canvas.focusOutEvent(QtGui.QFocusEvent(QtCore.QEvent.Type.FocusOut))
    # Simulate a release consumed by the other window, then return and click body.
    center=canvas.mapFromScene(image.sceneBoundingRect().center())
    QTest.mouseClick(canvas.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=center)
    restored=ImageItem(svg=image.toSvg())
    info={'displayed':[image.sceneBoundingRect().width(),image.sceneBoundingRect().height()], 'reloaded':[restored.sceneBoundingRect().width(),restored.sceneBoundingRect().height()], 'transform':[image.transform().m11(),image.transform().m22()], 'resize_active':image._resize_edge}
    (OUT/'image-interrupted.json').write_text(json.dumps(info,indent=2))
    assert abs(info['displayed'][0]-info['reloaded'][0])<.1,info
