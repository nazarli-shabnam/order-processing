"""
Setup file for shared events module.
This allows installing the shared module with: pip install -e .
"""
from setuptools import setup, find_packages

setup(
    name="event-driven-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
    ],
)

