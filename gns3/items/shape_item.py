# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Base class for shape items (Rectangle, ellipse etc.).
"""

import xml.etree.ElementTree as ET
from ..qt import QtCore, QtGui, QtWidgets
from .drawing_item import DrawingItem
from .utils import colorFromSvg

import logging
log = logging.getLogger(__name__)


class ShapeItem(DrawingItem):

    """
    Base class to draw shapes on the scene.
    """

    def __init__(self, width=200, height=200, svg=None, **kws):

        super().__init__(svg=svg, **kws)
        self.setAcceptHoverEvents(True)
        self._border = 5
        self._edge = None
        self._resize_snapshot = None
        self._originally_movable = True

        if svg is None:
            self.setRect(0, 0, width, height)
            pen = QtGui.QPen(QtCore.Qt.GlobalColor.black, 2, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
            self.setPen(pen)
            brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 255))  # default color is white and not transparent
            self.setBrush(brush)
        else:
            self.fromSvg(svg)
        if self._id is None:
            self.create()

    def mousePressEvent(self, event):
        """
        Handles all mouse press events.

        :param event: QMouseEvent instance
        """

        self.update()
        self._originally_movable = bool(self.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        if self.locked():
            self._edge = None
            QtWidgets.QGraphicsItem.mousePressEvent(self, event)
            return
        if event.pos().x() > (self.rect().right() - self._border):
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self._edge = "right"

        elif event.pos().x() < (self.rect().left() + self._border):
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self._edge = "left"

        elif event.pos().y() < (self.rect().top() + self._border):
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self._edge = "top"

        elif event.pos().y() > (self.rect().bottom() - self._border):
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self._edge = "bottom"
        if self._edge:
            self._resize_snapshot = (QtCore.QRectF(self.rect()), event.pos(), self.sceneTransform(), self.sceneTransform().inverted()[0])
        QtWidgets.QGraphicsItem.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """
        Handles all mouse release events.

        :param: QMouseEvent instance
        """

        self.update()
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, self._originally_movable and not self.locked())
        self._edge = None
        self._resize_snapshot = None
        QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        """
        Handles all mouse move events.

        :param event: QMouseEvent instance
        """

        self.update()
        if self._edge and self._resize_snapshot and not self.locked():
            rect, press, transform, inverse = self._resize_snapshot
            delta = inverse.map(event.scenePos()) - press
            resized = QtCore.QRectF(rect)
            if self._edge == 'left':
                resized.setLeft(rect.left() + delta.x())
            elif self._edge == 'right':
                resized.setRight(rect.right() + delta.x())
            elif self._edge == 'top':
                resized.setTop(rect.top() + delta.y())
            else:
                resized.setBottom(rect.bottom() + delta.y())
            resized = resized.normalized()
            resized.setWidth(max(1, resized.width()))
            resized.setHeight(max(1, resized.height()))
            from .group_item import set_scene_position
            self.setRect(0, 0, resized.width(), resized.height())
            set_scene_position(self, transform.map(resized.topLeft()))
            event.accept()
            return

        QtWidgets.QGraphicsItem.mouseMoveEvent(self, event)

    def hoverMoveEvent(self, event):
        """
        Handles all hover move events.

        :param event: QGraphicsSceneHoverEvent instance
        """

        # locked objects don't need cursors
        if not self.locked():
            if event.pos().x() > (self.rect().right() - self._border):
                self._graphics_view.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
            elif event.pos().x() < (self.rect().left() + self._border):
                self._graphics_view.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
            elif event.pos().y() < (self.rect().top() + self._border):
                self._graphics_view.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
            elif event.pos().y() > (self.rect().bottom() - self._border):
                self._graphics_view.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
            else:
                self._graphics_view.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        """
        Handles all hover leave events.

        :param event: QGraphicsSceneHoverEvent instance
        """

        # locked objects don't need cursors
        if not self.locked():
            self._graphics_view.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def setWidthAndHeight(self, width, height):
        self.setRect(0, 0, width, height)

    def fromSvg(self, svg):
        """
        Import element information from SVG
        """
        svg = ET.fromstring(svg)
        width = float(svg.get("width", self.rect().width()))
        height = float(svg.get("height", self.rect().height()))
        self.setRect(0, 0, width, height)

        pen = QtGui.QPen()
        brush = QtGui.QBrush(QtCore.Qt.BrushStyle.SolidPattern)

        if len(svg):
            pen = self._penFromSVGElement(svg[0])
            if svg[0].get("fill"):
                new_color = colorFromSvg(svg[0].get("fill"))
                color = brush.color()
                color.setBlue(new_color.blue())
                color.setRed(new_color.red())
                color.setGreen(new_color.green())
                brush.setColor(color)
            if svg[0].get("fill-opacity"):
                color = brush.color()
                color.setAlphaF(float(svg[0].get("fill-opacity")))
                brush.setColor(color)

        self.setPen(pen)
        self.setBrush(brush)
        self.update()
