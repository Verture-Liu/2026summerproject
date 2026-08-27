from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata


datas, binaries, hiddenimports = collect_all("multiqc")
datas += copy_metadata("multiqc", recursive=True)

a = Analysis(
    [str(Path(SPECPATH) / "multiqc_entry.py")],
    pathex=[],
    binaries=binaries,
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
    name="multiqc",
    console=True,
    debug=False,
    strip=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="multiqc")
