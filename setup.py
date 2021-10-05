"""pyvesync setup script."""

from os import path
from setuptools import setup, find_packages


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyvesync',
    version='1.4.1',
    description='pyvesync is a library to manage Etekcity\
                 Devices and Levoit Air Purifier',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/markperdue/pyvesync',
    author='Mark Perdue, Joe Trabulsy',
    author_email='webdjoe@gmail.com',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    keywords=['iot', 'vesync', 'levoit', 'etekcity'],
    packages=find_packages('src', exclude=['tests', 'tests.*']),
    package_dir={'': 'src'},
    zip_safe=False,
    install_requires=['requests>=2.20.0'],
    python_requires='>=3.6',
)
