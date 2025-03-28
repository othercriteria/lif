"""
Cython build script for Lif
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "lif.utils.cython_optimized",
        ["lif/utils/cython_optimized.pyx"],
        include_dirs=[np.get_include()],
    ),
]

setup(
    name="lif-cython",
    ext_modules=cythonize(extensions),
    zip_safe=False,
)