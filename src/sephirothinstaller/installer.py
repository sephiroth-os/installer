from pathlib import Path
import tempfile
import zipfile
import shutil
import requests
import subprocess
import winshell
import os
import json

class SephirothInstaller:
    def __init__(
            self,
            os_edition,
            install_path,
            progress_callback=None,
            data_path=None,
    ):
        self.edition = os_edition
        self.install_path = Path(install_path)

        self.data_path = (
            Path(data_path)
            if data_path
            else Path(os.getenv("APPDATA")) / "SephirothOS"
        )

        self.progress = (
                progress_callback
                or (lambda p, t: None)
        )

    def update(self, percent, text):
        self.progress(percent, text)


    def install(self):

        self.install_path.mkdir(
            parents=True,
            exist_ok=True
        )

        with tempfile.TemporaryDirectory() as tmp:

            tmp = Path(tmp)

            zip_path = tmp / "release.zip"
            extract_path = tmp / "extract"

            self.update(5, "Getting latest release...")

            api = (
                "https://api.github.com/repos/oxygen-me/SephirothOS-v2/releases/latest"
            )

            response = requests.get(api)
            response.raise_for_status()

            release = response.json()

            assets = release["assets"]

            if not assets:
                raise RuntimeError("The latest release has no downloadable assets.")

            asset = next(
                (a for a in assets if a["name"].lower().endswith(".zip")),
                None
            )

            if asset is None:
                raise RuntimeError("No .zip asset found in the latest release.")

            download_url = asset["browser_download_url"]


            self.update(10, "Downloading...")

            r = requests.get(
                download_url,
                stream=True
            )

            r.raise_for_status()

            total = int(
                r.headers.get(
                    "content-length",
                    0
                )
            )

            done = 0

            with open(zip_path, "wb") as f:

                for chunk in r.iter_content(8192):

                    f.write(chunk)

                    done += len(chunk)

                    if total:
                        self.update(
                            10 + int(done / total * 35),
                            "Downloading..."
                        )

            self.update(50, "Extracting...")

            with zipfile.ZipFile(zip_path) as z:
                z.extractall(extract_path)

            contents = list(extract_path.iterdir())

            if len(contents) == 1 and contents[0].is_dir():
                root = contents[0]
            else:
                root = extract_path

            self.update(70, "Installing files...")

            files = list(root.rglob("*"))

            total = len(files)

            for i, item in enumerate(files):

                relative = item.relative_to(root)
                destination = self.install_path / relative


                if item.is_dir():

                    destination.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                else:

                    destination.parent.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    shutil.copy2(
                        item,
                        destination
                    )


                self.update(
                    70 + int(i / total * 25),
                    "Installing files..."
                )

            self.update(
                98,
                "Cleaning up..."
            )

        target_dir = Path(str(os.getenv('APPDATA'))) / 'SephirothOS'
        target_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "edition": self.edition,
            "flag": "seth67",
            "upd": False
        }

        edition_path = Path(target_dir) / "license.json"

        with open(edition_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.update(
            100,
            "Installation complete!"
        )

        return release["tag_name"]

    def start_shortcut(self):
        start_menu = Path(winshell.start_menu())

        folder = start_menu / "Sephiroth"
        folder.mkdir(exist_ok=True)

        shortcut = folder / "SephirothOS.lnk"

        target = self.install_path / "SephirothOS.exe"

        with winshell.shortcut(str(shortcut)) as link:
            link.path = str(target)
            link.description = "SephirothOS"
            link.icon_location = (str(target), 0)
            link.working_directory = str(self.install_path)

    def create_shortcut(self):
        desktop = Path(winshell.desktop())
        shortcut = desktop / "SephirothOS.lnk"

        target = self.install_path / "SephirothOS.exe"

        with winshell.shortcut(str(shortcut)) as link:
            link.path = str(target)
            link.description = "SephirothOS"
            link.icon_location = (str(target), 0)
            link.working_directory = str(self.install_path)

    def launch_app(self):
        exe = self.install_path / "SephirothOS.exe"
        subprocess.Popen([str(exe)])