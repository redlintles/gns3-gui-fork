#!/usr/bin/env python3
"""Render real Qt widgets offline; transport is mocked, no appliances are started.
Run from the repository root: QT_QPA_PLATFORM=offscreen python3 scripts/render_readme_demos.py
Requires PyQt6, Pillow and the GUI dependencies. History uses committed server-test captures.
"""
import io
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Keep rendering independent from the user's desktop preferences.
config = tempfile.TemporaryDirectory(prefix='gns3-readme-')
os.environ['XDG_CONFIG_HOME'] = config.name
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys._called_from_test = True
from PIL import Image, ImageDraw, ImageFont
from gns3.qt import QtCore, QtGui, QtWidgets
from PyQt6.QtTest import QTest
from gns3.graphics_view import GraphicsView
from gns3.dialogs.text_editor_dialog import TextEditorDialog
from gns3.dialogs.image_properties_dialog import ImagePropertiesDialog
from gns3.items.image_item import ImageItem

from gns3.main_window import MainWindow
app = QtWidgets.QApplication([])
app.setStyle('Fusion')
out = Path('docs/media')
out.mkdir(exist_ok=True)
font = ImageFont.truetype('DejaVuSans.ttf', 18)
frames = []


def capture(widget, caption):
    app.processEvents()
    data = QtCore.QByteArray()
    buffer = QtCore.QBuffer(data)
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    widget.grab().save(buffer, 'PNG')
    compose(Image.open(io.BytesIO(bytes(data))).convert('RGB'), caption)


def compose(im, caption):
    im.thumbnail((880, 540))
    frame = Image.new('RGB', (900, 600), '#edf2f7')
    frame.paste(im, ((900-im.width)//2, 52+(540-im.height)//2))
    ImageDraw.Draw(frame).text((20, 16), caption, font=font, fill='#10243a')
    frames.append(frame)


def save(name):
    frames[0].save(out / (name+'.gif'), save_all=True, append_images=frames[1:],
                   duration=950, loop=0, optimize=True)
    print(name, len(frames), 'frames')
    frames.clear()


window = QtWidgets.QMainWindow()
view = GraphicsView(window)
window.setCentralWidget(view)
window.resize(880, 540)
main = MagicMock()
main.uiSnapToGridAction.isChecked.return_value = False
view._main_window = main
main.uiGraphicsView = view
instance_patch = patch.object(MainWindow, 'instance', return_value=main)
instance_patch.start()
view.toggleUiDeviceMenu = MagicMock()
view._topology = MagicMock()
view._topology.project.return_value = None
view._topology.links.return_value = []
window.show()
app.processEvents()


def note(text, x, y):
    item = view.createDrawingItem('text', x, y, 1, create=False)
    item.setPlainText(text)
    f = item.font(); f.setPointSize(22); item.setFont(f)
    return item


a = note('LAN 1', -180, -80)
b = note('LAN 2', 70, 30)
capture(view, 'Containers: select elements in your lab')
container = view._groups.add('Campus', [a, b])
capture(view, 'Container created: notes and drawings share a hierarchy')
for i in range(1, 5):
    container.setPos(container.pos()+QtCore.QPointF(25, 10))
    capture(view, 'Moving the container moves its children together')
container.setStyle(dict(shape='ellipse', fill_color='#2088aaee', border_color='#ff2463aa', border_width=3, border_style=1))
capture(view, 'Style: change the container shape and appearance')
save('containers')

for factor in (1, 1.1, 1.1, 1.1, 1/1.1, 1/1.1):
    view.scaleView(factor, QtCore.QPoint(470, 270))
    capture(view, 'Zoom: magnify around the chosen point')
QTest.mousePress(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(60, 430))
for x in (90, 130, 170):
    QTest.mouseMove(view.viewport(), QtCore.QPoint(x, 450))
    capture(view, 'Hand: drag an empty area to pan')
QTest.mouseRelease(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(170, 450))
save('navigation')

view.scene().clear(); view.resetTransform(); view.centerOn(0, 0)
view._adding_rectangle = True
QTest.mousePress(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(200, 170))
for x, y in ((240, 195), (300, 230), (400, 290), (490, 340)):
    QTest.mouseMove(view.viewport(), QtCore.QPoint(x, y))
    capture(view, 'Shapes: press and drag to define the size')
with patch('gns3.graphics_view.StyleEditorDialog.exec', return_value=QtWidgets.QDialog.DialogCode.Accepted):
    QTest.mouseRelease(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(490, 340))
capture(view, 'Confirm the style to create the shape; Esc cancels the draft')
save('shapes')

view.scene().clear(); view._adding_rectangle = False
view.addLine(True)
QTest.mouseClick(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(180, 180))
for x, y in ((250, 200), (330, 250), (460, 330), (600, 260)):
    event = QtGui.QMouseEvent(QtCore.QEvent.Type.MouseMove, QtCore.QPointF(x,y), QtCore.QPointF(view.viewport().mapToGlobal(QtCore.QPoint(x,y))), QtCore.Qt.MouseButton.NoButton, QtCore.Qt.MouseButton.NoButton, QtCore.Qt.KeyboardModifier.NoModifier)
    app.sendEvent(view.viewport(), event)
    capture(view, 'Lines: click to set the origin; move to preview')
with patch('gns3.dialogs.line_properties_dialog.LinePropertiesDialog.exec', return_value=QtWidgets.QDialog.DialogCode.Accepted):
    QTest.mouseClick(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(600,260))
capture(view, 'Click again to set the endpoint; confirm in Line properties')
save('lines')

view.scene().clear()
item = note('Network lab', -160, -30)
dialog = TextEditorDialog(view, [item]); dialog.show()
capture(dialog, 'Notes: choose text, font, size and styles before creation')
dialog.uiPlainTextEdit.setPlainText('Main campus\nNetwork lab')
dialog.fontSize.setValue(26); dialog.underline.setChecked(True)
capture(dialog, 'The text editor previews your typography')
dialog.accept(); capture(view, 'Confirm to apply the note to the canvas')
save('typography')

view.scene().clear()
dialog = ImagePropertiesDialog(view, 128, 128); dialog.show()
capture(dialog, 'Images: set dimensions before importing')
dialog.widthEdit.setValue(230)
capture(dialog, 'Keep aspect ratio synchronizes width and height')
dialog.close()
item = ImageItem(image_path='resources/images/gns3_icon_128x128.png', pos=QtCore.QPointF(-130,-130))
view.scene().addItem(item); item.setSelected(True)
for size in (128, 170, 210, 260):
    item.setDimensions(size, size)
    capture(view, 'Canvas image: dimensions and aspect ratio stored in SVG')
save('images')
window.close()
window.deleteLater()
app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)

# These are actual native screenshots already committed with real-server validation.
for filename, caption in [
    ('replay-before-undo.png', 'History: state before Undo'),
    ('replay-after-undo.png', 'Undo: previous membership and position restored'),
    ('replay-after-redo.png', 'Redo: reapply the operation'),
]:
    compose(Image.open(Path('docs/history/visibility')/filename).convert('RGB'), caption)
save('history')
