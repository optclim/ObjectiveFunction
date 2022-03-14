from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc

name = 'ObjectiveFunction'
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
        'numpy>=1.21.0',
        'pandas',
        'dfo-ls',
    ],
    cmdclass={'build_sphinx': BuildDoc},
    command_options={
        'build_sphinx': {
            'project': ('setup.py', name),
            'version': ('setup.py', version),
            'release': ('setup.py', release),
            'copyright': ('setup.py', author),
            'source_dir': ('setup.py', 'docs')}},
    setup_requires=['sphinx'],
    extras_require={
        'docs': [
            'sphinx<4.0',
            'sphinx_rtd_theme',
        ],
        'lint': [
            'flake8>=3.5.0',
        ],
        'testing': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'objfun-create-db = ObjectiveFunction.createdb:main',
            'objfun-nlopt = ObjectiveFunction.optimise:main',
            'objfun-dfols = ObjectiveFunction.dfols:main',
            'objfun-example-model = ObjectiveFunction.example:main',
        ],
    },
    author=author,
    description="ObjectiveFunction optimisation framework for cylc workflows",
)
