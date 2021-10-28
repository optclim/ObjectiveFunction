from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc

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
            'optclim2 = OptClim2.optimise:main',
            'optclim2-dfols = OptClim2.dfols:main',
            'optclim2-example-model = OptClim2.example:main',
        ],
    },
    author=author,
    description="OptClim2 optimisation framework for cylc workflows",
)
