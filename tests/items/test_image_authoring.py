from unittest.mock import MagicMock, patch
import pytest
from PyQt6.QtTest import QTest
from gns3.qt import QtCore, QtWidgets
from canvas_fixtures import canvas, drawing


@pytest.fixture
def image_path(tmp_path):
    from gns3.qt import QtGui
    path = tmp_path / 'image.png'
    image = QtGui.QImage(100, 50, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtGui.QColor('green'))
    image.save(str(path))
    return str(path)


@pytest.mark.parametrize('accept', [False, True])
def test_import_image_properties_transaction(canvas, image_path, accept):
    from gns3.items.image_item import ImageItem
    value = (400, 200, True) if accept else None
    with patch('gns3.dialogs.image_properties_dialog.ImagePropertiesDialog.getDimensions', return_value=value):
        canvas.addImage(image_path)
    images = [item for item in canvas.scene().items() if isinstance(item, ImageItem)]
    assert len(images) == int(accept)
    if accept:
        assert images[0].boundingRect().size() == QtCore.QSizeF(400, 200)
        copy = ImageItem(svg=images[0].toSvg())
        assert copy.boundingRect().size() == QtCore.QSizeF(400, 200)


@pytest.mark.parametrize('corner', ['tl', 'br'])
@pytest.mark.parametrize('keep', [True, False])
def test_image_corner_resize_preserves_opposite_corner_and_serializes(canvas, image_path, corner, keep):
    from gns3.items.image_item import ImageItem
    image = ImageItem(image_path=image_path, pos=QtCore.QPointF(100, 100))
    image.keep_aspect = keep
    canvas.scene().addItem(image)
    QtWidgets.QApplication.processEvents()
    r = image.boundingRect()
    point = r.topLeft() + QtCore.QPointF(2, 2) if corner == 'tl' else r.bottomRight() - QtCore.QPointF(2, 2)
    opposite = image.mapToScene(r.bottomRight() if corner == 'tl' else r.topLeft())
    start = canvas.mapFromScene(image.mapToScene(point))
    end = start + (QtCore.QPoint(-40, -30) if corner == 'tl' else QtCore.QPoint(40, 30))
    QTest.mousePress(canvas.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(canvas.viewport(), end)
    QTest.mouseRelease(canvas.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=end)
    assert image.boundingRect().width() > r.width()
    if keep:
        assert image.boundingRect().width() / image.boundingRect().height() == pytest.approx(2)
    fixed = image.mapToScene(image.boundingRect().bottomRight() if corner == 'tl' else image.boundingRect().topLeft())
    assert (fixed - opposite).manhattanLength() < 1
    restored = ImageItem(svg=image.toSvg())
    assert restored.boundingRect().size() == image.boundingRect().size()
    assert restored.keep_aspect is keep


def test_image_dimension_dialog_ratio_and_free_size(canvas):
    from gns3.dialogs.image_properties_dialog import ImagePropertiesDialog
    dialog = ImagePropertiesDialog(canvas, 100, 50)
    dialog.widthEdit.setValue(400)
    assert dialog.heightEdit.value() == 200
    dialog.keepAspect.setChecked(False)
    dialog.heightEdit.setValue(350)
    assert dialog.widthEdit.value() == 400
