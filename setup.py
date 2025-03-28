#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='lif',
      version='0.1.0',
      description='Game of Life variant with local dynamics',
      author='Daniel Klein',
      author_email='othercriteria@gmail.com',
      url='https://github.com/othercriteria/lif',
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'lif=lif.cli:run',
          ],
      },
      python_requires='>=3.4',
      )