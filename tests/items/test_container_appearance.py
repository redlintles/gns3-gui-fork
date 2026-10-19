from unittest.mock import MagicMock, patch
import pytest
from PyQt6.QtTest import QTest
from gns3.qt import QtCore, QtWidgets
from test_group_item import canvas, drawing, device


@pytest.mark.parametrize('shape', ['rect', 'triangle', 'ellipse'])
def test_container_style_roundtrip_and_rectangular_resize_bounds(canvas, shape):
    from test_group_item import group
    from gns3.items.group_item import GroupItem, read_group
    node = device(canvas, 100, 100)
    container = group(canvas, [node])
    position = node.scenePos()
    container.setStyle(dict(shape=shape, fill_color='#4088aa22', border_color='#ff123456',
                           border_width=6, border_style=2))
    svg = container.toSvg()
    copy = GroupItem(svg=svg)
    assert copy.style == container.style
    assert read_group(svg)['style']['shape'] == shape
    assert container.shape().contains(node.mapRectToParent(node.boundingRect().united(node.childrenBoundingRect())))
    position = node.scenePos()
    assert bool(container.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape) is (shape == 'rect')
    assert container.shape().contains(container.rect().topLeft() + QtCore.QPointF(1, 1)) is (shape == 'rect')
    canvas.enterGroup(container)
    container.setSelected(True)
    container.setDimensions(500, 350)
    for corner, point in container.corners().items():
        hit = canvas._groups.resizeHandleAt(container.mapToScene(point))
        assert hit == (container, corner)
    assert node.scenePos() == position


def test_container_dialog_has_accessible_exclusive_icon_choices(canvas):
    from gns3.dialogs.group_properties_dialog import GroupPropertiesDialog
    dialog = GroupPropertiesDialog(canvas, 'LAN', 500, 300)
    assert dialog.tabs.currentIndex() == 0
    editor = dialog.styleEditor
    assert editor.shape_buttons['rect'].isChecked()
    editor.shape_buttons['triangle'].click()
    assert editor.styleData()['shape'] == 'triangle'
    assert not editor.shape_buttons['rect'].isChecked()
    assert all(not button.text() and button.accessibleName() and not button.icon().isNull()
               for button in editor.shape_buttons.values())


def test_container_color_controls_remain_readable(canvas):
    from gns3.dialogs.container_style_widget import ContainerStyleWidget
    from gns3.qt import QtGui
    editor = ContainerStyleWidget()
    button = QtWidgets.QPushButton()
    editor.updateColorButton(button, '#00000000')
    assert button.text() == 'Transparent' and 'color: black' in button.styleSheet()
    editor.updateColorButton(button, '#ff000000')
    assert 'color: white' in button.styleSheet()
    assert isinstance(editor.style(), QtWidgets.QStyle)  # QWidget API is not shadowed.
