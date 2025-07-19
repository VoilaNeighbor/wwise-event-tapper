import sys

from PySide6.QtWidgets import QApplication

from wet.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Wwise Event Tapper")
    app.setApplicationVersion("0.1.0")

    # High DPI support is enabled by default in Qt6
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
