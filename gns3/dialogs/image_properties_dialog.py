# SPDX-License-Identifier: GPL-3.0-or-later
"""Image dimensions are SVG dimensions, not a transient item scale."""
from ..qt import QtCore, QtWidgets


class ImagePropertiesDialog(QtWidgets.QDialog):
    def __init__(self, parent, width, height):
        super().__init__(parent)
        self.setWindowTitle('Image properties')
        form = QtWidgets.QFormLayout(self)
        self.widthEdit = QtWidgets.QDoubleSpinBox(self)
        self.heightEdit = QtWidgets.QDoubleSpinBox(self)
        for field, value in [(self.widthEdit, width), (self.heightEdit, height)]:
            field.setRange(1, 1000000)
            field.setDecimals(2)
            field.setStyleSheet('QDoubleSpinBox, QDoubleSpinBox QLineEdit { background-color: white; color: black; selection-background-color: #3484c6; selection-color: white; }')
            field.setValue(value)
        self.keepAspect = QtWidgets.QCheckBox('Keep aspect ratio', self)
        self.keepAspect.setChecked(True)
        self.ratio = width / max(height, 1)
        form.addRow('Width:', self.widthEdit)
        form.addRow('Height:', self.heightEdit)
        form.addRow(self.keepAspect)
        self.widthEdit.valueChanged.connect(self.widthChanged)
        self.heightEdit.valueChanged.connect(self.heightChanged)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def widthChanged(self, value):
        if self.keepAspect.isChecked():
            width = max(self.widthEdit.minimum(), self.heightEdit.minimum() * self.ratio,
                        min(value, self.widthEdit.maximum(), self.heightEdit.maximum() * self.ratio))
            blockers = [QtCore.QSignalBlocker(field) for field in (self.widthEdit, self.heightEdit)]
            self.widthEdit.setValue(width)
            self.heightEdit.setValue(width / self.ratio)

    def heightChanged(self, value):
        if self.keepAspect.isChecked():
            self.widthChanged(value * self.ratio)

    @classmethod
    def getDimensions(cls, parent, width, height):
        dialog = cls(parent, width, height)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.widthEdit.value(), dialog.heightEdit.value(), dialog.keepAspect.isChecked()
        return None
