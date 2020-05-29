# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main_window.py'],
	pathex=['K:/labeling_tool'],
	binaries=[],
	datas=[
		('K:/labeling_tool/*.py', '.'),
		('K:/labeling_tool/mplwidget.py', '.'),
		('K:/labeling_tool/*.ui', '.'),
		('K:/labeling_tool/logo_b_rayZ.png', '.')
	],
	hiddenimports=["matplotlib", "pkg_resources.py2_warn"],
	hookspath=[],
	runtime_hooks=[],
	excludes=[],
	win_no_prefer_redirects=False,
	win_private_assemblies=False,
	cipher=block_cipher,
	noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
cipher=block_cipher)
			 
exe = EXE(pyz,
	a.scripts,
	a.binaries,
	a.zipfiles,
	a.datas,
	[],
	name='labeling_app',
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	runtime_tmpdir=None,
	console=False )
