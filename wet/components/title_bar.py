from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

_title_bar_style = """
    QFrame {
        background-color: #2c3e50;
        border-bottom: 1px solid #34495e;
    }
"""

_menu_button_style = """
    QPushButton {
        background: transparent;
        color: white;
        border: none;
        margin: 5px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
"""

_exit_button_style = """
    QPushButton {
        background: transparent;
        color: white;
        border: none;
        font-size: 14px;
        font-weight: bold;
        text-align: center;
        padding: 0px;
        margin: 0px;
    }
    QPushButton:hover {
        background-color: #e74c3c;
        border-radius: 2px;
    }
"""


class TitleBar(QFrame):
    def __init__(self) -> None:
        super().__init__()

        self.setFixedHeight(30)
        self.setStyleSheet(_title_bar_style)

        self.select_file_button = QPushButton("Select File")
        self.export_button = QPushButton("Export")
        self.exit_button = QPushButton("×")  # noqa: RUF001

        self.select_file_button.setStyleSheet(_menu_button_style)
        self.export_button.setStyleSheet(_menu_button_style)
        self.exit_button.setFixedSize(24, 24)
        self.exit_button.setStyleSheet(_exit_button_style)

        title_label = QLabel("Wwise Event Tapper")
        title_label.setStyleSheet("color: white; font-weight: bold")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(title_label)
        layout.addWidget(self.select_file_button)
        layout.addWidget(self.export_button)
        layout.addStretch()
        layout.addWidget(self.exit_button)
