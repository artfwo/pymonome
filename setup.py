#! /usr/bin/env python3

from setuptools import setup

with open('README.rst') as file:
    long_description = file.read()

setup(
    name='pymonome',
    author='Artem Popov',
    author_email='artfwo@gmail.com',
    url='https://github.com/artfwo/pymonome',
    description='a monome serialosc client in python',
    long_description=long_description,
    version='0.11.2',
    py_modules=['monome'],
    include_package_data=True,
    install_requires=[
        'aiosc'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Software Development :: Libraries',
    ],
    license='MIT'
)
