# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join as path_join
from setuptools import find_packages, setup

CURDIR = abspath(dirname(__file__))
SRC = path_join(CURDIR, 'src')

with open(path_join(SRC, 'rmkbridge', 'version.py')) as f:
    exec(f.read())

KEYWORDS = ('robotframework testing testautomation acceptancetesting atdd bdd'
            'reporting testreporting robotmk checkmk syntheticmonitoring junit'
            'gatling' 'zap' 'cypress' 'xunit')

SHORT_DESC = ('RobotmkBridge integrates the results of arbitrary testing tools into Checkmk.')              

with open(path_join(CURDIR, 'README.md'), 'r') as readme:
    LONG_DESCRIPTION = readme.read()

CLASSIFIERS = '''
Development Status :: 3 - Alpha
Programming Language :: Python :: 3 :: Only
Operating System :: OS Independent
Topic :: Software Development :: Testing
License :: OSI Approved :: MIT License
'''.strip().splitlines()

setup(name='robotframework-robotmk-bridge',
      author='Simon Meggle',
      author_email='mail@robotmk.org',
      url='https://github.com/elabit/robotmk-bridge',
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
