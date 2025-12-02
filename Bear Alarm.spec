# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/miguel/miguelbranco80/bear-alarm/src/main_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('/Users/miguel/miguelbranco80/bear-alarm/resources/sounds', 'resources/sounds'), ('/Users/miguel/miguelbranco80/bear-alarm/resources/icons', 'resources/icons')],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtCharts'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Bear Alarm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Users/miguel/miguelbranco80/bear-alarm/resources/icons/AppIcon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Bear Alarm',
)
app = BUNDLE(
    coll,
    name='Bear Alarm.app',
    icon='/Users/miguel/miguelbranco80/bear-alarm/resources/icons/AppIcon.icns',
    bundle_identifier='com.bearalarm.app',
)
