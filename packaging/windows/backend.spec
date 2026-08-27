from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_submodules


root = Path(SPECPATH).parents[1]
src = root / "src"
sys.path.insert(0, str(src))
datas = [
    (str(src / "research_agent/web"), "research_agent/web"),
    (str(src / "research_agent/resources"), "research_agent/resources"),
    (str(src / "research_agent/skill_packages"), "research_agent/skill_packages"),
]
hiddenimports = collect_submodules("research_agent") + [
    "keyring.backends.Windows",
    "win32ctypes",
]

a = Analysis(
    [str(Path(SPECPATH) / "backend_entry.py")],
    pathex=[str(src)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PaleoRigorBackend",
    console=False,
    debug=False,
    strip=False,
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PaleoRigorBackend",
)
