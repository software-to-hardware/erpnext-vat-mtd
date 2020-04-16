# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in uk_vat/__init__.py
from uk_vat import __version__ as version

setup(
	name='uk_vat',
	version=version,
	description='United Kingdom VAT Return and Making-Tax-Digital (MTD) submission',
	author='Software to Hardware Ltd',
	author_email='info@softwaretohardware.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
