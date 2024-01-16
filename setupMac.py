from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': [], 'include_files': ['Resources/'], 'includes': ['fitz.mupdf']}

base = 'gui'

executables = [
    Executable('Display.py', base=base, target_name = 'Autobookmark', icon='Resources/logo.ico')
]

setup(name='Autobookmark',
      version = '1.0',
      description = 'Bookmarks',
      options = {'build_exe': build_options},
      executables = executables)
