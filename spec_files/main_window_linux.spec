# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main_window.py'],
             pathex=['/media/mrv6/ADATA SD700/labeling_tool'],
             binaries=[],
             datas=[
			('/media/mrv6/ADATA SD700/labeling_tool/main_window.py', '.'),
			('/media/mrv6/ADATA SD700/labeling_tool/mplwidget.py', '.'),
			('/media/mrv6/ADATA SD700/labeling_tool/main_window.ui', '.')
			 ],
             hiddenimports=["matplotlib"],
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
          name='main_window',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )