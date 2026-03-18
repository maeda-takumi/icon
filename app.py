import json
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "URL Launcher"
DATA_DIR = Path.home() / ".url_launcher_sample"
DATA_FILE = DATA_DIR / "links.json"


DEFAULT_DATA = {
    "groups": [
        {"id": 1, "name": "仕事"},
        {"id": 2, "name": "開発"},
        {"id": 3, "name": "AI"},
    ],
    "links": [
        {"id": 1, "group_id": 1, "title": "Google Drive", "url": "https://drive.google.com/"},
        {"id": 2, "group_id": 1, "title": "Google Sheets", "url": "https://docs.google.com/spreadsheets/"},
        {"id": 3, "group_id": 2, "title": "GitHub", "url": "https://github.com/"},
        {"id": 4, "group_id": 2, "title": "Localhost", "url": "http://localhost/"},
        {"id": 5, "group_id": 3, "title": "ChatGPT", "url": "https://chatgpt.com/"},
    ],
}


def ensure_data_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)


def load_data():
    ensure_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_domain_text(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path
        host = host.replace("www.", "")
        return host or url
    except Exception:
        return url


def get_icon_text(title: str, url: str) -> str:
    text = (title or "").strip()
    if text:
        return text[0].upper()
    domain = get_domain_text(url)
    return domain[0].upper() if domain else "?"


class LinkDialog(QDialog):
    def __init__(self, parent=None, title="", url=""):
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

    def __init__(self, title: str, url: str):
        super().__init__()
        self.title = title
        self.url = url
        self.setObjectName("linkCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(180, 170)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.badge = QLabel("URL")
        self.badge.setObjectName("cardBadge")

        top_row.addWidget(self.badge)
        top_row.addStretch()

        self.icon_label = QLabel(get_icon_text(title, url))
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(62, 62)
        self.icon_label.setObjectName("iconLabel")

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("titleLabel")

        self.domain_label = QLabel(get_domain_text(url))
        self.domain_label.setAlignment(Qt.AlignCenter)
        self.domain_label.setWordWrap(True)
        self.domain_label.setObjectName("domainLabel")

        layout.addLayout(top_row)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1220, 760)

        self.data = load_data()
        self.current_group_id = None

        self.build_ui()
        self.apply_styles()
        self.load_groups()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)

        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(14)

        logo_label = QLabel("URL Hub")
        logo_label.setObjectName("logoLabel")

        sub_label = QLabel("よく使うURLをまとめて管理")
        sub_label.setObjectName("sidebarSubLabel")

        self.group_list = QListWidget()
        self.group_list.itemSelectionChanged.connect(self.on_group_changed)

        add_group_btn = QPushButton("＋ グループ追加")
        add_group_btn.clicked.connect(self.add_group)

        delete_group_btn = QPushButton("－ グループ削除")
        delete_group_btn.clicked.connect(self.delete_group)

        side_layout.addWidget(logo_label)
        side_layout.addWidget(sub_label)
        side_layout.addSpacing(4)
        side_layout.addWidget(self.group_list, 1)
        side_layout.addWidget(add_group_btn)
        side_layout.addWidget(delete_group_btn)

        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(18)

        self.header_card = QFrame()
        self.header_card.setObjectName("headerCard")
        header_card_layout = QVBoxLayout(self.header_card)
        header_card_layout.setContentsMargins(22, 18, 22, 18)
        header_card_layout.setSpacing(14)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(4)

        self.group_title_label = QLabel("グループを選択してください")
        self.group_title_label.setObjectName("groupTitle")

        desc_label = QLabel("登録したURLをアプリのように一覧表示して、1クリックで開けます")
        desc_label.setObjectName("descLabel")

        title_wrap.addWidget(self.group_title_label)
        title_wrap.addWidget(desc_label)

        top_bar.addLayout(title_wrap)
        top_bar.addStretch()

        add_link_btn = QPushButton("URL追加")
        add_link_btn.setObjectName("primaryButton")
        add_link_btn.clicked.connect(self.add_link)

        open_all_btn = QPushButton("このグループをまとめて開く")
        open_all_btn.clicked.connect(self.open_all_links_in_group)

        top_bar.addWidget(add_link_btn)
        top_bar.addWidget(open_all_btn)

        search_row = QHBoxLayout()
        search_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("タイトルやドメインで検索")
        self.search_input.textChanged.connect(self.refresh_links)

        search_row.addWidget(self.search_input)

        header_card_layout.addLayout(top_bar)
        header_card_layout.addLayout(search_row)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 8, 4, 8)
        self.grid_layout.setHorizontalSpacing(18)
        self.grid_layout.setVerticalSpacing(18)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_area.setWidget(self.grid_container)

        content_layout.addWidget(self.header_card)
        content_layout.addWidget(self.scroll_area, 1)

        root.addWidget(self.sidebar)
        root.addWidget(self.content, 1)

    def apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f6f8fc;
            }

            QWidget {
                color: #1e293b;
                font-size: 14px;
            }

            #sidebar {
                background: #eef4ff;
                border-right: 1px solid #dbe5f4;
            }

            #logoLabel {
                font-size: 26px;
                font-weight: 800;
                color: #2563eb;
                padding-top: 2px;
            }

            #sidebarSubLabel {
                color: #64748b;
                font-size: 12px;
                padding-bottom: 6px;
            }

            QListWidget {
                background: white;
                border: 1px solid #dbe5f4;
                border-radius: 18px;
                padding: 10px;
                outline: none;
            }

            QListWidget::item {
                background: transparent;
                border-radius: 12px;
                padding: 12px 12px;
                margin: 4px 0;
            }

            QListWidget::item:selected {
                background: #dbeafe;
                color: #1d4ed8;
                font-weight: 700;
            }

            QPushButton {
                background: white;
                border: 1px solid #d6e0ef;
                border-radius: 14px;
                padding: 11px 16px;
                font-size: 14px;
                font-weight: 600;
                color: #334155;
            }

            QPushButton:hover {
                background: #f8fbff;
                border: 1px solid #93c5fd;
            }

            #primaryButton {
                background: #2563eb;
                color: white;
                border: none;
            }

            #primaryButton:hover {
                background: #1d4ed8;
            }

            QLineEdit {
                background: white;
                border: 1px solid #d6e0ef;
                border-radius: 14px;
                padding: 12px 14px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #60a5fa;
            }

            #headerCard {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 24px;
            }

            #groupTitle {
                font-size: 28px;
                font-weight: 800;
                color: #0f172a;
            }

            #descLabel {
                color: #64748b;
                font-size: 13px;
            }

            QScrollArea {
                background: transparent;
            }

            #linkCard {
                background: white;
                border: 1px solid #e7edf5;
                border-radius: 24px;
            }

            #linkCard:hover {
                border: 1px solid #bfdbfe;
            }

            #cardBadge {
                background: #eff6ff;
                color: #2563eb;
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            }

            #iconLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #93c5fd,
                    stop:1 #2563eb
                );
                color: white;
                font-size: 28px;
                font-weight: 800;
                border-radius: 18px;
            }

            #titleLabel {
                color: #0f172a;
                font-size: 15px;
                font-weight: 700;
            }

            #domainLabel {
                color: #64748b;
                font-size: 12px;
            }

            QMenu {
                background: white;
                border: 1px solid #dbe5f4;
                border-radius: 10px;
                padding: 6px;
            }

            QMenu::item {
                padding: 8px 14px;
                border-radius: 8px;
            }

            QMenu::item:selected {
                background: #eff6ff;
            }
            """
        )

    def load_groups(self):
        self.group_list.clear()

        for group in self.data["groups"]:
            item = QListWidgetItem(group["name"])
            item.setData(Qt.UserRole, group["id"])
            self.group_list.addItem(item)

        if self.group_list.count() > 0:
            self.group_list.setCurrentRow(0)

    def on_group_changed(self):
        item = self.group_list.currentItem()
        if not item:
            self.current_group_id = None
            self.group_title_label.setText("グループを選択してください")
            self.refresh_links()
            return

        self.current_group_id = item.data(Qt.UserRole)
        self.group_title_label.setText(item.text())
        self.refresh_links()

    def clear_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_links(self):
        self.clear_grid()

        if self.current_group_id is None:
            return

        keyword = self.search_input.text().strip().lower()

        links = [
            link for link in self.data["links"]
            if link["group_id"] == self.current_group_id
        ]

        if keyword:
            links = [
                link for link in links
                if keyword in link["title"].lower() or keyword in get_domain_text(link["url"]).lower()
            ]

        columns = 5
        for index, link in enumerate(links):
            card = LinkCard(link["title"], link["url"])
            card.clicked.connect(lambda url=link["url"]: self.open_url(url))
            card.edit_requested.connect(lambda link_id=link["id"]: self.edit_link(link_id))
            card.delete_requested.connect(lambda link_id=link["id"]: self.delete_link(link_id))

            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)

    def open_url(self, url):
        webbrowser.open(url)

    def get_next_group_id(self):
        return max((g["id"] for g in self.data["groups"]), default=0) + 1

    def get_next_link_id(self):
        return max((l["id"] for l in self.data["links"]), default=0) + 1

    def add_group(self):
        name, ok = QInputDialog.getText(self, "グループ追加", "グループ名")
        if not ok or not name.strip():
            return

        self.data["groups"].append({
            "id": self.get_next_group_id(),
            "name": name.strip(),
        })
        save_data(self.data)
        self.load_groups()

        for i in range(self.group_list.count()):
            item = self.group_list.item(i)
            if item.text() == name.strip():
                self.group_list.setCurrentItem(item)
                break

    def delete_group(self):
        if self.current_group_id is None:
            return

        current_item = self.group_list.currentItem()
        if not current_item:
            return

        reply = QMessageBox.question(
            self,
            "確認",
            f"「{current_item.text()}」を削除しますか？\nこのグループ内のURLも削除されます。",
        )
        if reply != QMessageBox.Yes:
            return

        self.data["groups"] = [g for g in self.data["groups"] if g["id"] != self.current_group_id]
        self.data["links"] = [l for l in self.data["links"] if l["group_id"] != self.current_group_id]
        save_data(self.data)
        self.load_groups()

    def add_link(self):
        if self.current_group_id is None:
            QMessageBox.information(self, "案内", "先にグループを選択してください。")
            return

        dialog = LinkDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        title, url = dialog.get_values()

        self.data["links"].append({
            "id": self.get_next_link_id(),
            "group_id": self.current_group_id,
            "title": title,
            "url": url,
        })
        save_data(self.data)
        self.refresh_links()

    def edit_link(self, link_id):
        link = next((l for l in self.data["links"] if l["id"] == link_id), None)
        if not link:
            return

        dialog = LinkDialog(self, title=link["title"], url=link["url"])
        if dialog.exec() != QDialog.Accepted:
            return

        title, url = dialog.get_values()
        link["title"] = title
        link["url"] = url

        save_data(self.data)
        self.refresh_links()

    def delete_link(self, link_id):
        link = next((l for l in self.data["links"] if l["id"] == link_id), None)
        if not link:
            return

        reply = QMessageBox.question(self, "確認", f"「{link['title']}」を削除しますか？")
        if reply != QMessageBox.Yes:
            return

        self.data["links"] = [l for l in self.data["links"] if l["id"] != link_id]
        save_data(self.data)
        self.refresh_links()

    def open_all_links_in_group(self):
        if self.current_group_id is None:
            return

        links = [link for link in self.data["links"] if link["group_id"] == self.current_group_id]

        if not links:
            QMessageBox.information(self, "案内", "このグループにはURLがありません。")
            return

        for link in links:
            webbrowser.open(link["url"])


def main():
    app = QApplication(sys.argv)
    font = QFont("Yu Gothic UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()