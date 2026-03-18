from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.services import APP_NAME, LinkService
from ui.components import LinkCard, LinkDialog
from ui.styles import APP_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.default_window_size = (1220, 760)
        self.view_mode_window_size = (980, 640)
        self.resize(*self.default_window_size)

        self.service = LinkService()
        self.current_group_id = None
        self.is_view_mode = False

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

        self.add_group_btn = QPushButton("＋ グループ追加")
        self.add_group_btn.clicked.connect(self.add_group)

        self.delete_group_btn = QPushButton("－ グループ削除")
        self.delete_group_btn.clicked.connect(self.delete_group)

        side_layout.addWidget(logo_label)
        side_layout.addWidget(sub_label)
        side_layout.addSpacing(4)
        side_layout.addWidget(self.group_list, 1)
        side_layout.addWidget(self.add_group_btn)
        side_layout.addWidget(self.delete_group_btn)

        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(18)

        self.header_card = QFrame()
        self.header_card.setObjectName("headerCard")
        header_card_layout = QVBoxLayout(self.header_card)
        header_card_layout.setContentsMargins(22, 18, 22, 18)
        header_card_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(2)

        self.group_title_label = QLabel("グループを選択してください")
        self.group_title_label.setObjectName("groupTitle")

        desc_label = QLabel("登録したURLをアプリのように一覧表示して、1クリックで開けます")
        desc_label.setObjectName("descLabel")

        title_wrap.addWidget(self.group_title_label)
        title_wrap.addWidget(desc_label)

        top_bar.addLayout(title_wrap)
        top_bar.addStretch()

        self.mode_btn = QPushButton("ビューモード")
        self.mode_btn.setObjectName("modeButton")
        self.mode_btn.clicked.connect(self.toggle_view_mode)

        self.add_link_btn = QPushButton("URL追加")
        self.add_link_btn.setObjectName("primaryButton")
        self.add_link_btn.clicked.connect(self.add_link)

        self.open_all_btn = QPushButton("このグループをまとめて開く")
        self.open_all_btn.clicked.connect(self.open_all_links_in_group)

        top_bar.addWidget(self.mode_btn)
        top_bar.addWidget(self.add_link_btn)
        top_bar.addWidget(self.open_all_btn)

        self.search_container = QWidget()
        self.search_container.setObjectName("searchContainer")
        self.search_row = QHBoxLayout(self.search_container)
        self.search_row.setContentsMargins(0, 0, 0, 0)
        self.search_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("タイトルやドメインで検索")
        self.search_input.textChanged.connect(self.refresh_links)

        self.search_row.addWidget(self.search_input)

        self.pager_container = QWidget()
        self.pager_container.setObjectName("pagerContainer")
        pager_row = QHBoxLayout(self.pager_container)
        pager_row.setContentsMargins(0, 0, 0, 0)
        pager_row.setSpacing(8)
        pager_row.addStretch()

        self.prev_group_btn = QPushButton("◀")
        self.prev_group_btn.setObjectName("pagerButton")
        self.prev_group_btn.setFixedWidth(48)
        self.prev_group_btn.clicked.connect(self.select_prev_group)

        self.pager_label = QLabel("0 / 0")
        self.pager_label.setObjectName("pagerLabel")

        self.next_group_btn = QPushButton("▶")
        self.next_group_btn.setObjectName("pagerButton")
        self.next_group_btn.setFixedWidth(48)
        self.next_group_btn.clicked.connect(self.select_next_group)

        pager_row.addWidget(self.prev_group_btn)
        pager_row.addWidget(self.pager_label)
        pager_row.addWidget(self.next_group_btn)

        header_card_layout.addLayout(top_bar)
        header_card_layout.addWidget(self.search_container)
        header_card_layout.addWidget(self.pager_container)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 8, 4, 8)
        self.grid_layout.setHorizontalSpacing(16)
        self.grid_layout.setVerticalSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.scroll_area.setWidget(self.grid_container)

        content_layout.addWidget(self.header_card)
        content_layout.addWidget(self.scroll_area, 1)

        root.addWidget(self.sidebar)
        root.addWidget(self.content, 1)

    def apply_styles(self):
        self.setStyleSheet(APP_STYLE)

    def load_groups(self):
        self.group_list.clear()
        for group in self.service.get_groups():
            item = QListWidgetItem(group["name"])
            item.setData(Qt.UserRole, group["id"])
            self.group_list.addItem(item)

        if self.group_list.count() > 0:
            self.group_list.setCurrentRow(0)
        else:
            self.current_group_id = None
            self.group_title_label.setText("グループを選択してください")
            self.update_pager_label()
            self.refresh_links()

    def update_pager_label(self):
        count = self.group_list.count()
        row = self.group_list.currentRow()
        current = row + 1 if row >= 0 else 0
        self.pager_label.setText(f"{current} / {count}")
        enabled = count > 1
        self.prev_group_btn.setEnabled(enabled)
        self.next_group_btn.setEnabled(enabled)

    def on_group_changed(self):
        item = self.group_list.currentItem()
        if not item:
            self.current_group_id = None
            self.group_title_label.setText("グループを選択してください")
            self.update_pager_label()
            self.refresh_links()
            return

        self.current_group_id = item.data(Qt.UserRole)
        self.group_title_label.setText(item.text())
        self.update_pager_label()
        self.refresh_links()

    def select_prev_group(self):
        if self.group_list.count() < 2:
            return
        next_row = (self.group_list.currentRow() - 1) % self.group_list.count()
        self.group_list.setCurrentRow(next_row)

    def select_next_group(self):
        if self.group_list.count() < 2:
            return
        next_row = (self.group_list.currentRow() + 1) % self.group_list.count()
        self.group_list.setCurrentRow(next_row)

    def toggle_view_mode(self):
        self.is_view_mode = not self.is_view_mode
        self.mode_btn.setProperty("viewMode", self.is_view_mode)
        self.mode_btn.setText("編集モード" if self.is_view_mode else "ビューモード")
        self.mode_btn.style().unpolish(self.mode_btn)
        self.mode_btn.style().polish(self.mode_btn)

        self.sidebar.setVisible(not self.is_view_mode)
        self.add_link_btn.setVisible(not self.is_view_mode)
        self.open_all_btn.setVisible(not self.is_view_mode)
        self.search_container.setVisible(not self.is_view_mode)
        self.pager_container.setProperty("compact", self.is_view_mode)
        self.prev_group_btn.setProperty("compact", self.is_view_mode)
        self.next_group_btn.setProperty("compact", self.is_view_mode)
        self.pager_label.setProperty("compact", self.is_view_mode)
        for widget in (self.pager_container, self.prev_group_btn, self.next_group_btn, self.pager_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        if self.is_view_mode:
            self.resize(*self.view_mode_window_size)
        else:
            self.resize(*self.default_window_size)

        self.refresh_links()

    def clear_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()

    def refresh_links(self):
        self.clear_grid()

        keyword = "" if self.is_view_mode else self.search_input.text().strip().lower()
        links = self.service.get_filtered_links(self.current_group_id, keyword)

        columns = 4 if self.is_view_mode else 6
        for index, link in enumerate(links):
            card = LinkCard(
                link["title"],
                link["url"],
                favicon=self.service.get_favicon(link["url"]),
                compact=self.is_view_mode,
            )
            card.clicked.connect(lambda url=link["url"]: self.service.open_url(url))
            card.edit_requested.connect(lambda link_id=link["id"]: self.edit_link(link_id))
            card.delete_requested.connect(lambda link_id=link["id"]: self.delete_link(link_id))

            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)

    def add_group(self):
        name, ok = QInputDialog.getText(self, "グループ追加", "グループ名")
        if not ok or not name.strip():
            return

        group = self.service.add_group(name)
        self.load_groups()

        for i in range(self.group_list.count()):
            item = self.group_list.item(i)
            if item.data(Qt.UserRole) == group["id"]:
                self.group_list.setCurrentItem(item)
                break

    def delete_group(self):
        if self.current_group_id is None:
            return

        item = self.group_list.currentItem()
        if not item:
            return

        reply = QMessageBox.question(
            self,
            "確認",
            f"「{item.text()}」を削除しますか？\nこのグループ内のURLも削除されます。",
        )
        if reply != QMessageBox.Yes:
            return

        self.service.delete_group(self.current_group_id)
        self.load_groups()

    def add_link(self):
        if self.current_group_id is None:
            QMessageBox.information(self, "案内", "先にグループを選択してください。")
            return

        dialog = LinkDialog(self)
        if dialog.exec() != LinkDialog.Accepted:
            return

        title, url = dialog.get_values()
        self.service.add_link(self.current_group_id, title, url)
        self.refresh_links()

    def edit_link(self, link_id: int):
        link = self.service.find_link(link_id)
        if not link:
            return

        dialog = LinkDialog(self, title=link["title"], url=link["url"])
        if dialog.exec() != LinkDialog.Accepted:
            return

        title, url = dialog.get_values()
        self.service.update_link(link_id, title, url)
        self.refresh_links()

    def delete_link(self, link_id: int):
        link = self.service.find_link(link_id)
        if not link:
            return

        reply = QMessageBox.question(self, "確認", f"「{link['title']}」を削除しますか？")
        if reply != QMessageBox.Yes:
            return

        self.service.delete_link(link_id)
        self.refresh_links()

    def open_all_links_in_group(self):
        if self.current_group_id is None:
            return

        links = self.service.get_links_by_group(self.current_group_id)
        if not links:
            QMessageBox.information(self, "案内", "このグループにはURLがありません。")
            return

        self.service.open_urls([link["url"] for link in links])
