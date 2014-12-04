# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

version = __import__('linguist').__version__
root = os.path.abspath(os.path.dirname(__file__))

# Vagrant / tox workaround (http://bugs.python.org/issue8876#msg208792)
if os.environ.get('USER','') == 'vagrant':
    del os.link

with open(os.path.join(root, 'README.rst')) as f:
    README = f.read()

setup(
    name='django-linguist',
    version=version,
    description='Model translation for Django',
    long_description=README,
    author='Gilles Fabio',
    author_email='gilles.fabio@gmail.com',
    url='http://github.com/ulule/django-linguist',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
