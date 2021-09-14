from setuptools import setup, find_packages

name = 'OptClim2'
version = '0.1'
release = '0.1.0'
author = 'Magnus Hagdorn'

setup(
    name=name,
    packages=find_packages(),
    version=release,
    include_package_data=True,
    install_requires=[
        'configobj',
    ],
    extras_require={
        'lint': [
            'flake8>=3.5.0',
        ],
        'testing': [
            'pytest',
        ],
    },
    author=author,
    description="OptClim2 optimisation framework for cylc workflows",
)
