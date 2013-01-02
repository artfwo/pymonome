from distutils.core import setup

setup(
    name='pymonome',
    version='0.2',
    packages=['monome', ],
    license='COPYING',
    url='http://pypi.python.org/pypi/pymonome',
    description='a monome serialosc client in python',
    long_description=open('README').read(),
    install_requires=[
        "pyOSC >= 0.3",
        "pybonjour >= 1.1.1",
    ],
)
