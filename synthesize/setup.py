from setuptools import setup

setup(
    name='synthesize',
    version='0.5.0',
    py_modules=['synthesize'],
    entry_points={
        'console_scripts': ['synthesize = synthesize:run']
    },
)
