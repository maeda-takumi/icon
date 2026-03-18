from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QVBoxLayout,
)

from core.services import get_domain_text, get_initial_text


class LinkDialog(QDialog):
    def __init__(self, parent=None, title: str = "", url: str = ""):
        super().__init__(parent)
        self.setWindowTitle("URL登録")
        self.setModal(True)
        self.resize(420, 160)

        self.title_edit = QLineEdit(title)
        self.url_edit = QLineEdit(url)

        form = QFormLayout()
        form.addRow("タイトル", self.title_edit)
        form.addRow("URL", self.url_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def validate_and_accept(self):
        title = self.title_edit.text().strip()
        url = self.url_edit.text().strip()

        if not title:
            QMessageBox.warning(self, "入力エラー", "タイトルを入力してください。")
            return

        if not url:
            QMessageBox.warning(self, "入力エラー", "URLを入力してください。")
            return

        if not (url.startswith("http://") or url.startswith("https://")):
            QMessageBox.warning(self, "入力エラー", "URLは http:// または https:// から始めてください。")
            return

        self.accept()

    def get_values(self):
        return self.title_edit.text().strip(), self.url_edit.text().strip()


class LinkCard(QFrame):
    clicked = Signal()
    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self, title: str, url: str, favicon: QPixmap | None = None, compact: bool = False):
        super().__init__()
        self.title = title
        self.url = url
        self.setObjectName("linkCard")
        self.setProperty("compact", compact)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(148, 150 if compact else 170)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.icon_wrap = QLabel()
        self.icon_wrap.setObjectName("iconWrap")
        self.icon_wrap.setAlignment(Qt.AlignCenter)
        self.icon_wrap.setFixedSize(58, 58)

        if favicon and not favicon.isNull():
            icon = favicon.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_wrap.setPixmap(icon)
            self.icon_wrap.setText("")
        else:
            self.icon_wrap.setText(get_initial_text(title, url))
            self.icon_wrap.setStyleSheet("font-size: 24px; font-weight: 800; color: #111827;")

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("titleLabel")

        self.domain_label = QLabel(get_domain_text(url))
        self.domain_label.setAlignment(Qt.AlignCenter)
        self.domain_label.setWordWrap(True)
        self.domain_label.setObjectName("domainLabel")
        self.domain_label.setVisible(not compact)

        layout.addWidget(self.icon_wrap, alignment=Qt.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addWidget(self.domain_label)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        self.show_context_menu(event.globalPos())

    def show_context_menu(self, pos):
        menu = QMenu(self)

        edit_action = QAction("編集", self)
        delete_action = QAction("削除", self)

        edit_action.triggered.connect(self.edit_requested.emit)
        delete_action.triggered.connect(self.delete_requested.emit)

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(pos)
