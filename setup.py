# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join as path_join
from setuptools import find_packages, setup

CURDIR = abspath(dirname(__file__))
SRC = path_join(CURDIR, 'src')

with open(path_join(SRC, 'rmkbridge', 'version.py')) as f:
    exec(f.read())

KEYWORDS = ('robotframework testing testautomation acceptancetesting atdd bdd'
            'reporting testreporting robotmk checkmk syntheticmonitoring')

SHORT_DESC = ('RobotmkBridge is an extensible tool for Robot Framework that '
              'enables you to integrate the results of arbitrary other testing tools '
              'into Checkmk. It is based on robotframework-oxygen, written by Eficode Oy, '
              'and is designed to facilitate the monitoring of test automation.')

with open(path_join(CURDIR, 'README.md'), 'r') as readme:
    LONG_DESCRIPTION = readme.read()

CLASSIFIERS = '''
Development Status :: 5 - Production/Stable
Programming Language :: Python :: 3 :: Only
Operating System :: OS Independent
Topic :: Software Development :: Testing
License :: OSI Approved :: MIT License
'''.strip().splitlines()

setup(name='robotframework-robotmk-bridge',
      author='Simon Meggle',
      author_email='mail@robotmk.org',
      url='https://wwww.robotmk.org',
      license='MIT',
      install_requires=[
           'robotframework<7.0.0,>=6.0.0',
           'junitparser==4.0',
           'PyYAML>=3.13',
           'pydantic>=2.4.2'
      ],
      packages=find_packages(SRC),
      package_dir={'': 'src'},
      package_data={'rmkbridge': ['*.yml']},
      keywords=KEYWORDS,
      classifiers=CLASSIFIERS,
      version=VERSION,
      description=SHORT_DESC,
      long_description=LONG_DESCRIPTION,
      long_description_content_type="text/markdown")
