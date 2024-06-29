"""pyvesync setup script."""

from os import path
from setuptools import setup, find_packages


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyvesync',
    version='2.1.11',
    description='pyvesync is a library to manage Etekcity\
                 Devices, Cosori Air Fryers and Levoit Air \
                     Purifiers run on the VeSync app.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/webdjoe/pyvesync',
    author='Mark Perdue, Joe Trabulsy',
    author_email='webdjoe@gmail.com',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
    ],
    keywords=['iot', 'vesync', 'levoit', 'etekcity', 'cosori', 'valceno'],
    packages=find_packages('src', exclude=['tests', 'test*']),
    package_dir={'': 'src'},
    install_requires=['requests>=2.20.0'],
    extras_require={
        'dev': ['pytest', 'pytest-cov', 'yaml', 'tox']
    },
    python_requires='>=3.8',
)
