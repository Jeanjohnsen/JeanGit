from setuptools import setup

setup (
    name='jgit',
    version='1.0',
    packages=['jgit'],
    entry_points= {
        'console_scripts' : [
            'jgit = jgit.cli:main'
        ] 
    }
)