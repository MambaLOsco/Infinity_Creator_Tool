# PyInstaller spec for CreatorPack
# Run with: pyinstaller packaging.spec

block_cipher = None


def collect_data_files() -> list[tuple[str, str]]:
    return [
        ('creatorpack/app_cli/branding/caption_styles.ssa', 'branding'),
        ('creatorpack/examples/brand_default.yaml', 'examples'),
    ]


a = Analysis(
    ['creatorpack/app_cli/main.py'],
    pathex=['.'],
    binaries=[],
    datas=collect_data_files(),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='creatorpack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='creatorpack'
)
