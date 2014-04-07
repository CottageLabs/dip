from setuptools import setup, find_packages
import sys, os

setup(
    name='dip',
    version=0.1,
    description="SWORDv2 client environment",
    long_description="""\
DIP - Deposit Information Package, SWORDv2 client environment""",
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="sword-app atom sword2 http cli",
    author="Richard Jones",
    author_email='rich.d.jones@gmail.com',
    url="http://swordapp.org/",
    license='MIT',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=["sword2", "lxml"]
)
