"""Regression cases reduced from the exploratory audit."""
import json
from unittest.mock import patch
import pytest
from PyQt6.QtTest import QTest
from gns3.qt import QtCore, QtGui, QtWidgets
from test_group_item import canvas, drawing, group

@pytest.fixture(autouse=True)
def evidence(tmp_path):
    global OUT
    OUT = tmp_path

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


def state(v):
    return {k: bool(getattr(v, '_adding_' + k)) for k in ['note','rectangle','ellipse','line','link']}


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


@pytest.mark.parametrize('zoom', [.2, 1, 5])
def test_line_endpoint_glyph_remains_clickable_at_each_zoom(canvas, zoom):
    canvas.window().resize(900,700); canvas.window().show(); canvas.resize(850,650)
    canvas.setSceneRect(-500,-500,1000,1000)
    canvas._main_window.uiShowGridAction.isChecked.return_value=False
    canvas.setBackgroundBrush(QtGui.QColor('#303030'))
    line=canvas.createDrawingItem('line',0,0,0,create=False)
    line.setLine(0,0,100,0); line.setSelected(True)
    canvas.scale(zoom,zoom);canvas.centerOn(50,0);QTest.qWait(20)
    center=canvas.mapFromScene(line.mapToScene(line.line().p2()))
    image=canvas.viewport().grab().toImage()
    white=sum(all(channel>220 for channel in image.pixelColor(center.x(),y).getRgb()[:3])
              for y in range(center.y()-25,center.y()+26))
    assert 3 <= white <= 10, (zoom,white)
    assert canvas._lines.endpointAt(canvas.mapToScene(center+QtCore.QPoint(3,0)))==(line,1)
