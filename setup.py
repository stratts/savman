#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'pyyaml', 'requests', 'pypiwin32', 'tqdm', 'docopt'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='savman',
    version='0.0.1',
    description="A utility for backing up and managing saved games",
    long_description=readme + '\n\n' + history,
    author="strata8",
    author_email='strata8@outlook.com',
    url='https://github.com/strata8/savman',
    packages=[
        'savman',
    ],
    package_dir={'savman':
                 'savman'},
    package_data= {'savman': ['data/gamedata', 'data/custom.txt']},
    entry_points={
        'console_scripts': [
            'savman = savman.app:main',
            'vbackup = savman.vbackup:main'
            ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='savman',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
