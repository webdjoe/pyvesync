"""pyvesync setup script."""

from setuptools import setup, find_packages


setup(
    name='pyvesync',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Home Automation',
    ],
    packages=find_packages('src', exclude=['tests', 'test*']),
    package_dir={'': 'src'},
)
