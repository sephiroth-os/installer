from idlelib.colorizer import prog_group_name_to_tag

import requests
from installer import SephirothInstaller
from PySide6.QtWidgets import QApplication, QWidget
from pathlib import Path
import os

edition = "standard"
program_files = os.environ.get(
    "ProgramFiles",
    r"C:\Program Files",
)

install_path = (
    Path(program_files)
    / "Oxygen"
    / "SephirothOS"
)

class InstallerApp:
    def __init__(self, argv: list[str]):
        self.qt = QApplication(argv)
        self.shell = None

    def run(self) -> int:
        self.shell = InstallerUI(self)
        self.shell.show()
        return self.qt.exec()

class InstallerUI(QWidget):
    def __init__(self, application):
        super().__init__()

        self.application = application

        self.setWindowTitle("Install SephirothOS")
        self.resize(600, 300)