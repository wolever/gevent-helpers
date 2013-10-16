#!/usr/bin/env python

# NOTE: We need this little hack to make sure that tox will run correctly from
# a different directory (ex 'python ../django-switchuser/setup.py develop').
import os
os.chdir(os.path.dirname(__file__) or ".")

from setuptools import setup, find_packages

try:
    long_description = open("README.rst", "U").read()
except IOError:
    long_description = "See https://github.com/wolever/gevent-helpers"

version = "0.1.0"
setup(
    name="gevent-helpers",
    version=version,
    url="https://github.com/wolever/gevent-helpers",
    author="David Wolever",
    author_email="david@wolever.net",
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license="BSD",
    classifiers=[ x.strip() for x in """
        Development Status :: 4 - Beta
        Intended Audience :: Developers
        License :: OSI Approved :: BSD License
        Natural Language :: English
        Operating System :: OS Independent
        Programming Language :: Python
    """.split("\n") if x.strip() ],
)
