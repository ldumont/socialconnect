#!/usr/bin/env python2.5

import os, sys

# project root dir
project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
#project_dir2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
site_packages_dir = os.path.abspath(os.path.join(project_root_dir, 'site-packages'))


# This is because portable WSGI applications should not write to sys.stdout or 
# use the 'print' statement without specifying an alternate file object 
# besides sys.stdout as the target.
#sys.stdout = sys.stderr

for path in (site_packages_dir, project_root_dir, project_dir):
    if path not in sys.path:
        sys.path.insert(0, path)
        

os.environ['DJANGO_SETTINGS_MODULE'] = 'yasn_example.settings'
os.environ['PYTHON_EGG_CACHE'] = os.path.join(project_root_dir, 'tmp')


from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
