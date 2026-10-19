from unittest.mock import MagicMock, patch
import pytest
from PyQt6.QtTest import QTest
from gns3.qt import QtCore, QtWidgets
from test_group_item import canvas, drawing, device


def test_zero_width_hides_shape_and_container_borders(canvas):
    from test_group_item import group
    item = drawing(canvas)
    container = group(canvas, [item])
    container.setStyle(dict(border_width=0))
    from unittest.mock import MagicMock
    painter = MagicMock()
    container.paint(painter, None)
    assert painter.setPen.call_args_list[0].args[0].style() == QtCore.Qt.PenStyle.NoPen
    assert container.style['border_width'] == 0
