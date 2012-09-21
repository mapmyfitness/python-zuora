#!/usr/bin/python -tt

setupArgs = {
    'name': 'zuora',
    'version': '1.0',
    'author': 'MapMyFitness',
    'author_email': 'brandon.fredericks@mapmyfitness.com',
    'url': 'ssh://git@git.mapmyfitness.com/suez',
    'description': 'Zuora client library.',
    'packages': ['zuora'],
}

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup
else:
    import sys
    import subprocess

    class TestRunner(Command):
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            errno = subprocess.call(['py.test'])
            sys.exit(errno)

    setupArgs.update({
        'tests_require': ['pytest'],
        'cmdclass': {'test': TestRunner},
        'install_requires': ['suds >= 0.4'],
        'zip_safe': False,
    })

setup(**setupArgs)
