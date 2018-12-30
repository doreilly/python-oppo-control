# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='oppo-control',
    version='0.1',
    packages=['oppo_control'],
    include_package_data=True,
    license='MIT License',
    description='A package for monitoring and controlling an Oppo UDP/BDP via RS-232C.',
    long_description=README,
    author='Dennis O’Reilly',
    author_email='dennis@doreilly.org',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
