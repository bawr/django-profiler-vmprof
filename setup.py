#!/usr/bin/env python

import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-profiler-vmprof',
    version='0.2.2',
    install_requires=[
        'django>=2.0',
        'psutil>=5.2.1',
        'vmprof>=0.4.9',
    ],
    python_requires='~=3.6',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='A minimalist VMProf integration for Django.',
    long_description=README,
    url='https://github.com/bawr/django-profiler-vmprof',
    author='Bartosz Wróblewski',
    author_email='bawr@hszm.pl',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
