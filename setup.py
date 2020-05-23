# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in cloud_extel/__init__.py
from cloud_extel import __version__ as version

setup(
	name='cloud_extel',
	version=version,
	description='Custom App for business specific customizations',
	author='Frappe',
	author_email='test@example.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
