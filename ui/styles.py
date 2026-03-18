APP_STYLE = """
QMainWindow {
    background: #f3f5f9;
}

QWidget {
    color: #0f172a;
    font-size: 14px;
}

#sidebar {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}

#logoLabel {
    font-size: 24px;
    font-weight: 800;
    color: #111827;
}

#sidebarSubLabel {
    color: #6b7280;
    font-size: 12px;
}

QListWidget {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 8px;
}

QListWidget::item {
    border-radius: 10px;
    padding: 10px 12px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background: #111827;
    color: white;
    font-weight: 700;
}

QPushButton {
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 600;
    color: #1f2937;
}

QPushButton:hover {
    background: #f9fafb;
}

#primaryButton {
    background: #111827;
    color: white;
    border: 1px solid #111827;
}

#primaryButton:hover {
    background: #1f2937;
}

#modeButton {
    background: #e5e7eb;
    color: #111827;
    border: 1px solid #d1d5db;
}

#modeButton[viewMode="true"] {
    background: #111827;
    color: white;
}

#headerCard {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
}

#groupTitle {
    font-size: 26px;
    font-weight: 800;
}

#descLabel {
    color: #6b7280;
    font-size: 12px;
}

#pagerLabel {
    font-size: 13px;
    color: #4b5563;
    font-weight: 600;
}
#pagerContainer[compact="true"] {
    margin-top: 2px;
}

#pagerButton[compact="true"] {
    min-width: 30px;
    max-width: 30px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 9px;
    padding: 2px 4px;
    font-size: 11px;
}

#pagerLabel[compact="true"] {
    font-size: 11px;
}


#viewModeFrame {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 22px;
}
QLineEdit {
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    padding: 10px 12px;
}

QLineEdit:focus {
    border: 1px solid #6b7280;
}

QScrollArea {
    background: transparent;
}

#linkCard {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
}

#linkCard:hover {
    border: 1px solid #9ca3af;
}

#linkCard[compact="true"] {
    border-radius: 16px;
}

#iconWrap {
    background: #f3f4f6;
    border-radius: 16px;
}

#titleLabel {
    color: #111827;
    font-size: 14px;
    font-weight: 700;
}

#domainLabel {
    color: #6b7280;
    font-size: 11px;
}

QMenu {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 6px;
}

QMenu::item {
    border-radius: 8px;
    padding: 8px 12px;
}

QMenu::item:selected {
    background: #f3f4f6;
}
"""
