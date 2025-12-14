"""
Setup file for shared events module.
This allows installing the shared module with: pip install -e .
"""
from setuptools import setup, find_packages

setup(
    name="event-driven-shared",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only Python standard library
        # dataclasses and enum are built-in for Python 3.7+
    ],
    description="Shared event schemas and utilities for event-driven architecture",
    author="Event-Driven Architecture Team",
)
