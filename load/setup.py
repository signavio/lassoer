from setuptools import setup

setup(
    name='load',
    version='0.3.0',
    py_modules=['load'],
    entry_points={
        'console_scripts': ['load = load:run']
    },
)
