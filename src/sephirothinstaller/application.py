from PySide6.QtCore import QUrl

import assets.resources_rc
import requests
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

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

global_version = None

url = f"https://api.github.com/sephiroth-os/sephirothos/releases/latest"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    global_version = data["tag_name"]
    print(global_version)
else:
    # raise ConnectionError(f"Unable to retrieve latest release. (Status Code: {response.status_code})")
    pass

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

        self.audio = QAudioOutput()
        self.player = QMediaPlayer()

        self.player.setAudioOutput(self.audio)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.audio.setVolume(0.15)

        self.player.setSource(QUrl("qrc:/assets/InstallerMusic.mp3"))
        self.player.play()