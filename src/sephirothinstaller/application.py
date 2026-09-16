from PySide6.QtCore import QUrl, Qt, QThread, Signal
from PySide6.QtGui import QPixmap

import assets.resources_rc
import requests
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from installer import SephirothInstaller
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy, QStackedWidget, \
    QPushButton
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

    volume = 0.15

    def __init__(self, argv: list[str]):
        self.qt = QApplication(argv)
        self.shell = None

        self.audio = QAudioOutput()
        self.player = QMediaPlayer()

        self.player.setAudioOutput(self.audio)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.audio.setVolume(self.volume)

        self.player.setSource(QUrl("qrc:/assets/InstallerMusic.mp3"))

    def run(self) -> int:
        self.shell = InstallerUI(self)
        self.shell.show()
        self.player.play()
        return self.qt.exec()

    def mute_music(self) -> None:
        self.volume += 0.05
        self.audio.setVolume(self.volume)


class InstallerUI(QWidget):
    def __init__(self, application):
        super().__init__()

        self.application = application

        self.setWindowTitle("Install SephirothOS")
        self.setStyleSheet("background-color: #1c1c1c")
        self.resize(600, 300)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.watermark = QLabel()
        self.watermark.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.watermark.setScaledContents(True)

        pixmap = QPixmap("watermark.png")

        self.watermark.setPixmap(pixmap)
        self.watermark.show()

        self.content_area = QWidget()
        self.content_area.setStyleSheet("background-color: #121212;")

        self.layout.addWidget(self.watermark, 1)
        self.layout.addWidget(self.content_area, 2)

        self.main_layout.addLayout(self.layout, 1)

        # static footer
        self.footer = QWidget()
        self.footer.setStyleSheet("background-color: #1c1c1c;")

        self.footer_layout = QHBoxLayout(self.footer)
        self.footer_layout.setContentsMargins(10, 10, 10, 10)
        self.footer_layout.setSpacing(0)

        self.backbutton = QPushButton("Back")
        self.backbutton.setStyleSheet("""
                QPushButton {
                background-color: #171717;
                color: white;
                font-family: Segoe UI;
                font-size: 14px;
                font-weight: 600;
                padding: 4px 20px;
                }
                QPushButton:hover {
                background-color: #1c1c1c;
                }
                QPushButton:pressed {
                background-color: #101010;
                }""")

        self.nextbutton = QPushButton("Next")
        self.nextbutton.setStyleSheet("""
                        QPushButton {
                        background-color: #171717;
                        color: white;
                        font-family: Segoe UI;
                        font-size: 14px;
                        font-weight: 600;
                        padding: 4px 20px;
                        }
                        QPushButton:hover {
                        background-color: #1c1c1c;
                        }
                        QPushButton:pressed {
                        background-color: #101010;
                        }""")

        self.footer_layout.addWidget(self.backbutton)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.nextbutton)

        self.main_layout.addWidget(self.footer)

        # stack
        self.contentlayout = QVBoxLayout(self.content_area)
        self.contentlayout.setContentsMargins(0, 0, 0, 0)
        self.contentlayout.setSpacing(0)

        self.stack = QStackedWidget()

        self.stack.addWidget(WelcomePage(self.application))

        self.contentlayout.addWidget(self.stack)

        self.stack.setCurrentIndex(0)


class WelcomePage(QWidget):
    def __init__(self, application):
        super().__init__()

        self.application = application

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(20, 20, 20, 20)
        self.mainlayout.setSpacing(0)
        self.mainlayout.addStretch()

        self.title = QLabel("Sephiroth")
        self.title.setStyleSheet("background-color: transparent; font-family: Segoe UI; font-size: 56px; font-weight: 800; font-style: italic;")
        self.mainlayout.addWidget(self.title)

        self.subtitle = QLabel("Welcome to the your Sephiroth Sephiroth wizard.")
        self.subtitle.setStyleSheet("background-color: transparent; font-family: Segoe UI; font-size: 16px; font-weight: 400; font-style: italic;")
        self.mainlayout.addWidget(self.subtitle)

        self.mainlayout.addStretch()

        self.mutebutton = QPushButton("Mute Music")
        self.mutebutton.setStyleSheet("""
        QPushButton {
        background-color: #171717;
        color: white;
        font-family: Segoe UI;
        font-size: 14px;
        font-weight: 600;
        padding: 4px 20px;
        }
        QPushButton:hover {
        background-color: #1c1c1c;
        }
        QPushButton:pressed {
        background-color: #101010;
        }""")
        self.mutebutton.pressed.connect(self.application.mute_music)
        self.mainlayout.addWidget(self.mutebutton, alignment=Qt.AlignmentFlag.AlignRight)


class PluginsPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application


class AngryPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application


class PathPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application


class ReadyPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application


class InstallPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application


class InstallThread(QThread):

    progress = Signal(int, str)

    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path

    def run(self):
        installer = SephirothInstaller(
            edition,
            self.install_path,
            self.progress.emit
        )

        installer.install()


class DonePage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application

