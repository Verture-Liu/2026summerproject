from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata


datas, binaries, hiddenimports = collect_all("multiqc")
# MultiQC's Conda environment contains optional dependencies whose package
# metadata is not always discoverable (for example, pyarrow).  The frozen
# executable only needs MultiQC's own metadata; recursively copying every
# dependency metadata makes the build fail before analysis begins.
datas += copy_metadata("multiqc")

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
    target_arch="arm64",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="multiqc",
)
