#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup, find_packages

from brick import version

file_name = os.path.join('requirements', 'common.txt')
with open(file_name, 'r') as r:
    requirements = [l for l in r.read().splitlines()]

setup(
    name='brick',
    version=version,
    description='Brick Iot',

    author='Massimiliano Ravelli',
    author_email='massimiliano.ravelli@gmail.com',
    url='http://github.com/madron/brick-iot',

    license='MIT',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: System :: Automation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='iot mqtt',

    packages=find_packages(),
    install_requires=requirements,
    entry_points = dict(
        console_scripts=['brick=brick.__main__:main'],
    )
)