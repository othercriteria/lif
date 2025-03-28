#!/usr/bin/env python

from setuptools import setup

setup(name = 'lif',
      version = '0.1.0',
      description = 'Game of Life variant with local dynamics',
      author = 'Daniel Klein',
      author_email = 'othercriteria@gmail.com',
      url = 'https://github.com/othercriteria/lif',
      scripts = ['lif.py'],
      python_requires='>=3.4',
      )