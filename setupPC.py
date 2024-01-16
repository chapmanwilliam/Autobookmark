from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': [], 'include_files': ['Resources/']}

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('Display.py', base=base, target_name = 'Autobookmarker')
]

setup(name='Autobookmark',
      version = '1',
      description = 'Bookmarks correspondence',
      options = {'build_exe': build_options},
      executables = executables)
