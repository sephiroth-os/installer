import sys

from sephirothinstaller.application import InstallerApp

def main() -> int:
    application = InstallerApp(sys.argv)
    return application.run()

if __name__ == "__main__":
    raise SystemExit(main())