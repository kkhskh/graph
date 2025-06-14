from setuptools import setup, find_packages

setup(
    name="graph_heal",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'networkx',
        'matplotlib',
        'numpy'
    ]
) 