from setuptools import setup, find_packages

setup(
    name='merlin2',
    version='0.1',
    packages=find_packages(),
    description='Driver for Merlin2 chip, test and evaluation board.',
    author='Christian Hahn',
    author_email='christian@kumunetworks.com',
    license='',
    install_requires=[
        'pyftdi',
        'numpy',
    ],
)
