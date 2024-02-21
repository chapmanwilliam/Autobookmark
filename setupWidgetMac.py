from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': ["fitz"], 'excludes': [], 'include_files': ['Resources/','Images/'],
                 'includes': ['fitz.mupdf'],'build_exe': 'buildMacWidget/',
                 'zip_include_packages': ['encodings', "PyQt6"]}

import sys

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('AutoBookmarker.py', base=base, target_name = 'AutobookmarkerMacWidget', icon='Resources/logo.ico')
]

setup(name='Autobookmark',
      version = '1.1',
      description = 'Bookmarks',
      options = {'build_exe': build_options},
      executables = executables)
