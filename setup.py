from distutils.core import setup

setup(
    name='pymonome',
    version='0.2.2',
    packages=['monome', ],
    author='Artem Popov',
    url='http://pypi.python.org/pypi/pymonome',
    description='a monome serialosc client in python',
    long_description=open('README').read(),
    install_requires=[
        "pyOSC >= 0.3",
        "pybonjour >= 1.1.1",
    ],
)
