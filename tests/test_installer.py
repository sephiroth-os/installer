import io
import json
import zipfile

import pytest

from sephirothinstaller.installer import SephirothInstaller


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeResponse:
    """Small fake requests.Response for testing."""

    def __init__(self, data=None, content=b"", status_error=None):
        self._data = data
        self.content = content
        self.status_error = status_error
        self.headers = {
            "content-length": str(len(content))
        }

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        return self._data

    def iter_content(self, chunk_size=8192):
        # Split the content into chunks to behave more like requests.
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i:i + chunk_size]


def make_fake_zip():
    """
    Create a fake SephirothOS release ZIP entirely in memory.
    """

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "SephirothOS/SephirothOS.exe",
            "fake executable",
        )

        z.writestr(
            "SephirothOS/config.json",
            '{"test": true}',
        )

        z.writestr(
            "SephirothOS/data/example.txt",
            "hello from test",
        )

    return buffer.getvalue()


def make_release_response():
    """Create a fake GitHub release API response."""

    return FakeResponse(
        data={
            "tag_name": "v2.0.0",
            "assets": [
                {
                    "name": "SephirothOS.zip",
                    "browser_download_url": (
                        "https://example.com/SephirothOS.zip"
                    ),
                }
            ],
        }
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_installer_initialization(tmp_path):
    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path,
    )

    assert installer.edition == "standard"
    assert installer.install_path == tmp_path
    assert callable(installer.progress)


def test_installer_custom_progress_callback(tmp_path):
    updates = []

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path,
        progress_callback=lambda percent, text: updates.append(
            (percent, text)
        ),
    )

    installer.update(50, "Testing...")

    assert updates == [
        (50, "Testing...")
    ]


def test_default_progress_callback_does_not_crash(tmp_path):
    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path,
    )

    installer.update(50, "Testing...")


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

def test_install(monkeypatch, tmp_path):
    """
    Test a complete installation using a fake GitHub release
    and a fake ZIP file.
    """

    install_path = tmp_path / "SephirothOS"

    # Keep APPDATA out of the real user's machine.
    fake_appdata = tmp_path / "AppData"

    monkeypatch.setenv(
        "APPDATA",
        str(fake_appdata),
    )

    fake_zip = make_fake_zip()

    responses = iter([
        make_release_response(),
        FakeResponse(content=fake_zip),
    ])

    def fake_get(*args, **kwargs):
        return next(responses)

    monkeypatch.setattr(
        "sephirothinstaller.installer.requests.get",
        fake_get,
    )

    updates = []

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=install_path,
        progress_callback=lambda percent, text: updates.append(
            (percent, text)
        ),
    )

    tag = installer.install()

    # Correct release version was returned.
    assert tag == "v2.0.0"

    # Files from the ZIP were installed.
    assert (
        install_path / "SephirothOS.exe"
    ).exists()

    assert (
        install_path / "config.json"
    ).exists()

    assert (
        install_path / "data" / "example.txt"
    ).exists()

    # Check the actual contents of a copied file.
    assert (install_path / "config.json").read_text(encoding="utf-8") == '{"test": true}'

    # License file was created.
    license_file = (
        fake_appdata
        / "SephirothOS"
        / "license.json"
    )

    assert license_file.exists()

    with license_file.open(
        "r",
        encoding="utf-8",
    ) as f:
        license_data = json.load(f)

    assert license_data == {
        "edition": "standard",
        "flag": "seth67",
        "upd": False,
    }

    # Progress should have reached 100.
    assert updates[-1] == (
        100,
        "Installation complete!",
    )


def test_install_handles_zip_with_no_root_directory(
    monkeypatch,
    tmp_path,
):
    """
    Test a ZIP whose files are directly at the root rather than
    inside a SephirothOS/ directory.
    """

    install_path = tmp_path / "SephirothOS"

    fake_appdata = tmp_path / "AppData"

    monkeypatch.setenv(
        "APPDATA",
        str(fake_appdata),
    )

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as z:
        z.writestr(
            "SephirothOS.exe",
            "fake executable",
        )

    fake_zip = buffer.getvalue()

    responses = iter([
        make_release_response(),
        FakeResponse(content=fake_zip),
    ])

    monkeypatch.setattr(
        "sephirothinstaller.installer.requests.get",
        lambda *args, **kwargs: next(responses),
    )

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=install_path,
    )

    tag = installer.install()

    assert tag == "v2.0.0"

    assert (
        install_path / "SephirothOS.exe"
    ).exists()


# ---------------------------------------------------------------------------
# GitHub/API failures
# ---------------------------------------------------------------------------

def test_install_fails_when_no_assets(
    monkeypatch,
    tmp_path,
):
    response = FakeResponse(
        data={
            "tag_name": "v2.0.0",
            "assets": [],
        }
    )

    monkeypatch.setattr(
        "sephirothinstaller.installer.requests.get",
        lambda *args, **kwargs: response,
    )

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path,
    )

    with pytest.raises(
        RuntimeError,
        match="latest release has no downloadable assets",
    ):
        installer.install()


def test_install_fails_when_no_zip_exists(
    monkeypatch,
    tmp_path,
):
    response = FakeResponse(
        data={
            "tag_name": "v2.0.0",
            "assets": [
                {
                    "name": "SephirothOS.exe",
                    "browser_download_url": (
                        "https://example.com/SephirothOS.exe"
                    ),
                }
            ],
        }
    )

    monkeypatch.setattr(
        "sephirothinstaller.installer.requests.get",
        lambda *args, **kwargs: response,
    )

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path,
    )

    with pytest.raises(
        RuntimeError,
        match="No .zip asset found",
    ):
        installer.install()


def test_install_handles_http_error(
    monkeypatch,
    tmp_path,
):
    response = FakeResponse(
        status_error=RuntimeError("HTTP error")
    )

    monkeypatch.setattr(
        "sephirothinstaller.installer.requests.get",
        lambda *args, **kwargs: response,
    )

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path,
    )

    with pytest.raises(
        RuntimeError,
        match="HTTP error",
    ):
        installer.install()


# ---------------------------------------------------------------------------
# launch_app
# ---------------------------------------------------------------------------

def test_launch_app(monkeypatch, tmp_path):
    calls = []

    def fake_popen(command):
        calls.append(command)

    monkeypatch.setattr(
        "sephirothinstaller.installer.subprocess.Popen",
        fake_popen,
    )

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path,
    )

    installer.launch_app()

    assert calls == [
        [str(tmp_path / "SephirothOS.exe")]
    ]


# ---------------------------------------------------------------------------
# Desktop shortcut
# ---------------------------------------------------------------------------

def test_create_shortcut(monkeypatch, tmp_path):
    """
    Test create_shortcut() without touching the actual desktop.
    """

    desktop = tmp_path / "Desktop"
    desktop.mkdir()

    monkeypatch.setattr(
        "sephirothinstaller.installer.winshell.desktop",
        lambda: str(desktop),
    )

    captured = {}

    class FakeShortcut:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def __setattr__(self, name, value):
            if name != "_initialized":
                captured[name] = value

            object.__setattr__(
                self,
                name,
                value,
            )

    def fake_shortcut(path):
        captured["shortcut_path"] = path
        return FakeShortcut()

    monkeypatch.setattr(
        "sephirothinstaller.installer.winshell.shortcut",
        fake_shortcut,
    )

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path / "SephirothOS",
    )

    installer.create_shortcut()

    assert captured["shortcut_path"] == str(
        desktop / "SephirothOS.lnk"
    )

    assert captured["path"] == str(
        tmp_path / "SephirothOS" / "SephirothOS.exe"
    )

    assert captured["description"] == "SephirothOS"

    assert captured["icon_location"] == (
        str(
            tmp_path
            / "SephirothOS"
            / "SephirothOS.exe"
        ),
        0,
    )

    assert captured["working_directory"] == str(
        tmp_path / "SephirothOS"
    )


# ---------------------------------------------------------------------------
# Start Menu shortcut
# ---------------------------------------------------------------------------

def test_start_shortcut(monkeypatch, tmp_path):
    """
    Test start_shortcut() without touching the real Start Menu.
    """

    start_menu = tmp_path / "StartMenu"
    start_menu.mkdir()

    monkeypatch.setattr(
        "sephirothinstaller.installer.winshell.start_menu",
        lambda: str(start_menu),
    )

    captured = {}

    class FakeShortcut:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def __setattr__(self, name, value):
            if name != "_initialized":
                captured[name] = value

            object.__setattr__(
                self,
                name,
                value,
            )

    def fake_shortcut(path):
        captured["shortcut_path"] = path
        return FakeShortcut()

    monkeypatch.setattr(
        "sephirothinstaller.installer.winshell.shortcut",
        fake_shortcut,
    )

    installer = SephirothInstaller(
        os_edition="standard",
        install_path=tmp_path / "SephirothOS",
    )

    installer.start_shortcut()

    expected_folder = (
        start_menu / "Sephiroth"
    )

    assert expected_folder.exists()

    assert captured["shortcut_path"] == str(
        expected_folder / "SephirothOS.lnk"
    )

    assert captured["path"] == str(
        tmp_path
        / "SephirothOS"
        / "SephirothOS.exe"
    )

    assert captured["description"] == "SephirothOS"

    assert captured["icon_location"] == (
        str(
            tmp_path
            / "SephirothOS"
            / "SephirothOS.exe"
        ),
        0,
    )

    assert captured["working_directory"] == str(
        tmp_path / "SephirothOS"
    )
