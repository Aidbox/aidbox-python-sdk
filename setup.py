#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from io import open

from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('aidbox_python_sdk')

with open('README.md') as f:
    long_description = f.read()

setup(
    name='aidbox_python_sdk',
    version=version,
    url='http://github.com/Aidbox/aidbox-python-sdk',
    license='',
    description='Aidbox SDK for python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='fhir',
    author='beda.software',
    author_email='aidbox-python-sdk@beda.software',
    packages=['aidbox_python_sdk'],
    include_package_data=True,
    install_requires=[ 
        'uvloop>=0.13.0',
        'aiohttp>=3.6.2',
        'SQLAlchemy>=1.3.10',
        'fhirpy>=1.1.0',
        'aidboxpy>=1.1.0',
        'coloredlogs'
    ],
    tests_require=[
        'pytest>=3.6.1', 'pytest-asyncio>=0.10.0', 'responses>=0.10.8'
    ],
    zip_safe=False,
    project_urls={
        "Source Code": "https://github.com/Aidbox/aidbox-python-sdk",
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
