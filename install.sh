#!/bin/bash

# Clean previous setups
rm -rf dist
rm -rf build
rm -rf TestiPy.egg-info


# Create new setup
python3 setup.py sdist bdist_wheel


# Install locally
pip install dist/TestiPy-*-py3-none-any.whl


# Clean current setup
rm -rf dist
rm -rf build
rm -rf TestiPy.egg-info
