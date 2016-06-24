#!/usr/bin/env python3

import ats.client

from setuptools import setup, find_packages

PROJECT = 'ats.client'

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=ats.client.version,

    description='AiC python services, core client functions',
    long_description=long_description,

    author='AiC Project',
    author_email='aic-project@alterway.fr',

    install_requires=[
        'cliff',
        'requests',
        'pyflakes',
    ],

    extras_require={
        'docs': (
            'sphinx',
            'sphinx_rtd_theme',
        )},
    namespace_packages=['ats'],
    packages=find_packages(),
    include_package_data=True,

    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'asynctest'],

    zip_safe=False,
)
