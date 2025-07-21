import logging
import sys

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from wet.components.main_window import AppMainWindow
from wet.util import REPO_ROOT

_logger = logging.getLogger("wwise-event-tapper")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = QApplication(sys.argv)

    # Apply global styles.
    # -- qt_material must be imported after Qt.
    from qt_material import apply_stylesheet  # type: ignore

    apply_stylesheet(
        app,
        theme="light_blue.xml",
        invert_secondary=True,
        extra={"density_scale": "-1"},
    )

    # Load font & set antialiasing.
    path = REPO_ROOT / "assets" / "Roboto-VariableFont_wdth,wght.ttf"
    font_id = QFontDatabase.addApplicationFont(str(path))
    if font_families := QFontDatabase.applicationFontFamilies(font_id):
        font = QFont(font_families[0], 11)
    else:
        _logger.error("Failed to get font families from Roboto font")
        font = app.font()
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)

    # Init window and run app until end.
    window = AppMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
