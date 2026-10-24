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
capture(view, 'Containers: selecione elementos do laboratorio')
container = view._groups.add('Campus', [a, b])
capture(view, 'Container criado: notas e desenhos ficam na mesma hierarquia')
for i in range(1, 5):
    container.setPos(container.pos()+QtCore.QPointF(25, 10))
    capture(view, 'Mover o container transporta seus filhos')
container.setStyle(dict(shape='ellipse', fill_color='#2088aaee', border_color='#ff2463aa', border_width=3, border_style=1))
capture(view, 'Style: mude a forma e a aparencia do container')
save('containers')

for factor in (1, 1.1, 1.1, 1.1, 1/1.1, 1/1.1):
    view.scaleView(factor, QtCore.QPoint(470, 270))
    capture(view, 'Zoom: ampliar e reduzir ao redor do ponto escolhido')
QTest.mousePress(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(60, 430))
for x in (90, 130, 170):
    QTest.mouseMove(view.viewport(), QtCore.QPoint(x, 450))
    capture(view, 'Hand: arraste uma area vazia para navegar')
QTest.mouseRelease(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(170, 450))
save('navigation')

view.scene().clear(); view.resetTransform(); view.centerOn(0, 0)
view._adding_rectangle = True
QTest.mousePress(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(200, 170))
for x, y in ((240, 195), (300, 230), (400, 290), (490, 340)):
    QTest.mouseMove(view.viewport(), QtCore.QPoint(x, y))
    capture(view, 'Formas: pressione e arraste para definir o tamanho')
with patch('gns3.graphics_view.StyleEditorDialog.exec', return_value=QtWidgets.QDialog.DialogCode.Accepted):
    QTest.mouseRelease(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(490, 340))
capture(view, 'Confirmar o estilo cria a forma; Esc cancela o rascunho')
save('shapes')

view.scene().clear(); view._adding_rectangle = False
view.addLine(True)
QTest.mouseClick(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(180, 180))
for x, y in ((250, 200), (330, 250), (460, 330), (600, 260)):
    event = QtGui.QMouseEvent(QtCore.QEvent.Type.MouseMove, QtCore.QPointF(x,y), QtCore.QPointF(view.viewport().mapToGlobal(QtCore.QPoint(x,y))), QtCore.Qt.MouseButton.NoButton, QtCore.Qt.MouseButton.NoButton, QtCore.Qt.KeyboardModifier.NoModifier)
    app.sendEvent(view.viewport(), event)
    capture(view, 'Linhas: primeiro clique fixa a origem; mova para prever')
with patch('gns3.dialogs.line_properties_dialog.LinePropertiesDialog.exec', return_value=QtWidgets.QDialog.DialogCode.Accepted):
    QTest.mouseClick(view.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(600,260))
capture(view, 'Segundo clique define a ponta; confirme em Line properties')
save('lines')

view.scene().clear()
item = note('Laboratorio de redes', -160, -30)
dialog = TextEditorDialog(view, [item]); dialog.show()
capture(dialog, 'Notas: texto, familia, tamanho e estilos na criacao')
dialog.uiPlainTextEdit.setPlainText('Campus principal\nLaboratorio de redes')
dialog.fontSize.setValue(26); dialog.underline.setChecked(True)
capture(dialog, 'A caixa de texto mostra a previa da tipografia')
dialog.accept(); capture(view, 'Confirme para aplicar a nota ao canvas')
save('typography')

view.scene().clear()
dialog = ImagePropertiesDialog(view, 128, 128); dialog.show()
capture(dialog, 'Imagens: defina dimensoes antes de importar')
dialog.widthEdit.setValue(230)
capture(dialog, 'Keep aspect ratio sincroniza largura e altura')
dialog.close()
item = ImageItem(image_path='resources/images/gns3_icon_128x128.png', pos=QtCore.QPointF(-130,-130))
view.scene().addItem(item); item.setSelected(True)
for size in (128, 170, 210, 260):
    item.setDimensions(size, size)
    capture(view, 'Imagem no canvas: dimensoes e proporcao preservadas no SVG')
save('images')
window.close()
window.deleteLater()
app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)

# These are actual native screenshots already committed with real-server validation.
for filename, caption in [
    ('replay-before-undo.png', 'Historico: estado antes de desfazer'),
    ('replay-after-undo.png', 'Undo: associacao e posicao anteriores restauradas'),
    ('replay-after-redo.png', 'Redo: reaplique a operacao'),
]:
    compose(Image.open(Path('docs/history/visibility')/filename).convert('RGB'), caption)
save('history')
