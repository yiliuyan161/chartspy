#!/usr/bin/env python
# coding=utf-8

import os

from setuptools import setup, find_packages

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


def _parse_requirement_file(path):
    if not os.path.isfile(path):
        return []
    with open(path) as f:
        requirements = [line.strip() for line in f if line.strip()]
    return requirements


def get_install_requires():
    requirement_file = os.path.join(THIS_FOLDER, "requirements.txt")
    return _parse_requirement_file(requirement_file)


setup(
    name="chartspy",
    version="2.0.3",
    url="https://chartspy.icopy.site/",
    description="echarts g2plot klinechart highcharts tabulator python wrapper",
    keywords='echarts g2plot klinechart highcharts tabulator python ',
    packages=find_packages(exclude=("tests", "tests.*")),
    author="yiliuyan",
    author_email="yiliuyan161@126.com",
    maintainer="yiliuyan",
    maintainer_email="yiliuyan161@126.com",
    package_data={'': ['*.*']},
    long_description="",
    long_description_content_type='text/markdown',
    install_requires=get_install_requires(),
    zip_safe=False,
    platforms=["all"],
    classifiers=[
        'Programming Language :: Python',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
)
