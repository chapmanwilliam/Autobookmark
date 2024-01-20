from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': [], 'include_files': ['Resources/', 'Images/'],'includes': ['fitz.mupdf'],
                 'build_exe': 'buildMacWidget/'}

for dbmodule in ['dbhash', 'gdbm', 'dbm', 'dumbdbm']:
    try:
        __import__(dbmodule)
    except ImportError:
        pass
    else:
        # If we found the module, ensure it's copied to the build directory.
        build_options['packages'].append(dbmodule)

import sys

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('Autobookmarker.py', base=base, target_name='AutobookmarkerMacWidget', icon='Resources/logo.ico')
]

setup(name='Autobookmark',
      version='1.1',
      description='Bookmarks correspondence widget',
      options={'build_exe': build_options},
      executables=executables)
