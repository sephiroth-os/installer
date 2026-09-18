from PySide6.QtCore import QUrl, Qt, QThread, Signal
from PySide6.QtGui import QPixmap

import sephirothinstaller.assets.resources2_rc
import sephirothinstaller.assets.resources_rc

import requests
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

from installer import SephirothInstaller
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy, QStackedWidget, \
    QPushButton, QFileDialog, QLineEdit, QFrame, QMessageBox, QProgressBar, QCheckBox
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

url = f"https://api.github.com/repos/sephiroth-os/sephirothos/releases/latest"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    global_version = data["tag_name"]
    print(global_version)
else:
    raise ConnectionError(f"Unable to retrieve latest release. (Status Code: {response.status_code})")
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

    def pause_music(self) -> None:
        self.player.pause()

    def play_music(self) -> None:
        if not self.player.isPlaying():
            self.player.play()


class InstallerUI(QWidget):

    index = 0

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
                }
                QPushButton:disabled {
                color: #808080;
                }
                """)
        self.backbutton.setDisabled(True)

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
                        }
                        QPushButton:disabled {
                        color: #808080;
                        }
                        """)

        self.nextbutton.clicked.connect(self.turn_page)
        self.backbutton.clicked.connect(self.retreat)

        self.footer_layout.addWidget(self.backbutton)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.nextbutton)

        self.main_layout.addWidget(self.footer)

        # stack
        self.contentlayout = QVBoxLayout(self.content_area)
        self.contentlayout.setContentsMargins(0, 0, 0, 0)
        self.contentlayout.setSpacing(0)

        self.stack = QStackedWidget()

        self.welcome_page = WelcomePage(self.application)
        self.plugins_page = PluginsPage(self.application)
        self.angry_page = AngryPage(self.application)
        self.path_page = PathPage(self.application)
        self.ready_page = ReadyPage(self.application)
        self.install_page = InstallPage(self.application)
        self.done_page = DonePage(self.application)

        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.plugins_page)
        self.stack.addWidget(self.angry_page)
        self.stack.addWidget(self.path_page)
        self.stack.addWidget(self.ready_page)
        self.stack.addWidget(self.install_page)
        self.stack.addWidget(self.done_page)

        self.contentlayout.addWidget(self.stack)

        self.stack.setCurrentIndex(0)

    def turn_page(self):
        self.index += 1
        self.stack.setCurrentIndex(self.index)

        if self.index == 2:
            self.application.pause_music()
            self.angry_page.player.play()
        else:
            self.application.play_music()
            self.angry_page.player.stop()

        if self.index == 4:
            self.nextbutton.setText("Install")

        if self.index != 0:
            self.backbutton.setDisabled(False)

        if self.index == 5:
            if (Path(install_path) / "SephirothOS.exe").is_file():
                reply = QMessageBox.warning(
                    self, "Installation Found",
                    "An installation of SephirothOS already exists at the target path. Are you sure you want to proceed?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.stack.setCurrentIndex(5)
                    self.nextbutton.setDisabled(True)
                    self.backbutton.setDisabled(True)
                    self.install_page.start_install()
                else:
                    self.stack.setCurrentIndex(4)
                    self.index = 4

            else:
                reply = QMessageBox.question(
                    self, "Confirm Installation",
                    "The latest version of SephirothOS will be installed on your device. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.stack.setCurrentIndex(5)
                    self.nextbutton.setDisabled(True)
                    self.backbutton.setDisabled(True)
                    self.install_page.start_install()
                else:
                    self.stack.setCurrentIndex(4)
                    self.index = 4

        if self.index == 6:
            self.nextbutton.setText("Finish")
            self.backbutton.setDisabled(True)

        if self.index == 7:
            self.finish()

    def finish(self):
        installer = SephirothInstaller(edition, install_path)

        if self.done_page.shortcut.isChecked():
            installer.create_shortcut()

        if self.done_page.launch.isChecked():
            installer.launch_app()

        if self.done_page.startmenu.isChecked():
            installer.start_shortcut()

        QApplication.quit()

    def retreat(self):
        if self.index > 0:
            self.index -= 1
            self.stack.setCurrentIndex(self.index)

        if self.index == 0:
            self.backbutton.setDisabled(True)

        if self.index == 2:
            self.application.pause_music()
            self.angry_page.player.play()
        else:
            self.application.play_music()
            self.angry_page.player.stop()

        if self.index != 4:
            self.nextbutton.setText("Next")


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

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(20, 20, 20, 20)
        self.mainlayout.setSpacing(0)
        self.mainlayout.addStretch()

        self.title = QLabel("Add Plugins")
        self.title.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 56px; font-weight: 800; font-style: italic;")
        self.mainlayout.addWidget(self.title)

        self.subtitle = QLabel("Whale soon...")
        self.subtitle.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 16px; font-weight: 400; font-style: italic;")
        self.mainlayout.addWidget(self.subtitle)

        self.mainlayout.addStretch()


class AngryPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(20, 20, 20, 20)
        self.mainlayout.setSpacing(0)

        self.player = QMediaPlayer(self)

        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.3)
        self.player.setAudioOutput(self.audio)

        self.video = QVideoWidget(self)
        self.player.setVideoOutput(self.video)

        self.player.setSource(QUrl("qrc:/video/WakeUp.mp4"))

        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.setPlaybackRate(1)

        self.video.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.video.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)

        self.mainlayout.addWidget(self.video, 1)


class PathPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(20, 20, 20, 20)
        self.mainlayout.setSpacing(0)

        self.mainlayout.addStretch()

        self.title = QLabel("Install Location")
        self.title.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 36px; font-weight: 800; font-style: italic;")
        self.mainlayout.addWidget(self.title)

        self.subtitle = QLabel("The installer will create the directory if it doesn't exist.")
        self.subtitle.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 16px; font-weight: 400; font-style: italic;")
        self.mainlayout.addWidget(self.subtitle)

        self.mainlayout.addSpacing(10)

        self.path = QLineEdit(str(install_path))
        self.path.textChanged.connect(self.set_path)

        self.browse = QPushButton("Browse...")
        self.browse.clicked.connect(self.select_folder)

        layout = QHBoxLayout()
        layout.addWidget(self.path)
        layout.addWidget(self.browse)

        self.mainlayout.addLayout(layout)

        self.mainlayout.addStretch()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose installation folder",
            self.path.text()
        )

        if folder:
            self.path.setText(folder)

    def set_path(self):
        global install_path
        install_path = self.path.text()


class ReadyPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(20, 20, 20, 20)
        self.mainlayout.setSpacing(0)

        self.mainlayout.addStretch()

        self.title = QLabel("Ready to Install?")
        self.title.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 36px; font-weight: 800; font-style: italic;")
        self.mainlayout.addWidget(self.title)

        self.subtitle = QLabel("We put all your shit here so you can double-check.")
        self.subtitle.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 16px; font-weight: 400; font-style: italic;")
        self.mainlayout.addWidget(self.subtitle)
        self.mainlayout.addSpacing(10)

        self.div = QFrame()
        self.div.setFrameShape(QFrame.Shape.HLine)
        self.div.setStyleSheet("border: 1px solid #808080")
        self.div.setFixedHeight(1)
        self.mainlayout.addWidget(self.div)
        self.mainlayout.addSpacing(10)

        self.pathlabel = QLabel()
        self.editionlabel = QLabel()
        self.versionlabel = QLabel()

        self.pathlabel.setStyleSheet("font-family: Segoe UI; font-size: 16px; font-weight: 500;")
        self.editionlabel.setStyleSheet("font-family: Segoe UI; font-size: 16px; font-weight: 500;")
        self.versionlabel.setStyleSheet("font-family: Segoe UI; font-size: 16px; font-weight: 500;")

        self.mainlayout.addWidget(self.pathlabel)
        self.mainlayout.addWidget(self.editionlabel)
        self.mainlayout.addWidget(self.versionlabel)

        self.mainlayout.addStretch()

        self.update_info()

    def update_info(self):
        self.pathlabel.setText("Installing to: " + str(install_path))
        self.editionlabel.setText("Selected Edition: " + edition + " (you can't change this lmao)")
        self.versionlabel.setText("Version to Install: " + str(global_version))


class InstallPage(QWidget):
    def __init__(self, application):
        super().__init__()
        self.application = application

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(20, 20, 20, 20)
        self.mainlayout.setSpacing(0)

        self.mainlayout.addStretch()

        self.title = QLabel("Installing...")
        self.title.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 36px; font-weight: 800; font-style: italic;")
        self.mainlayout.addWidget(self.title)
        self.mainlayout.addSpacing(10)

        self.status = QLabel("Preparing installer...")
        self.status.setStyleSheet(
            "font-family: Segoe UI;"
            "font-size: 16px;"
        )
        self.mainlayout.addWidget(self.status)

        self.mainlayout.addSpacing(10)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.mainlayout.addWidget(self.progress)

        self.mainlayout.addStretch()

    def start_install(self):
        self.thread = InstallThread(install_path)

        self.thread.progress.connect(
            self.update_progress
        )

        self.thread.finished.connect(
            self.install_finished
        )

        self.thread.start()

    def update_progress(self, value, text):
        self.progress.setValue(value)
        self.status.setText(text)

    def install_finished(self):
        self.progress.setValue(100)
        self.status.setText("Installation complete!")
        self.application.shell.nextbutton.setText("Next")
        self.application.shell.nextbutton.setDisabled(False)


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

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(20, 20, 20, 20)
        self.mainlayout.setSpacing(0)

        self.mainlayout.addStretch()

        self.title = QLabel("Complete")
        self.title.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 36px; font-weight: 800; font-style: italic;")
        self.mainlayout.addWidget(self.title)

        self.subtitle = QLabel("Fuck you and have a nice day.")
        self.subtitle.setStyleSheet(
            "background-color: transparent; font-family: Segoe UI; font-size: 16px; font-weight: 400; font-style: italic;")
        self.mainlayout.addWidget(self.subtitle)
        self.mainlayout.addSpacing(10)

        self.shortcut = QCheckBox("Create Desktop Shortcut")
        self.launch = QCheckBox("Launch SephirothOS")
        self.startmenu = QCheckBox("Create Start Menu Shortcut")

        boxes = [self.shortcut, self.launch, self.startmenu]
        for i in boxes:
            i.setStyleSheet("background-color: transparent; color: white")

        self.shortcut.setChecked(False)
        self.launch.setChecked(True)
        self.startmenu.setChecked(True)

        self.mainlayout.addWidget(self.launch)
        self.mainlayout.addWidget(self.startmenu)
        self.mainlayout.addWidget(self.shortcut)

        self.mainlayout.addStretch()