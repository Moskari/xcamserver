'''
Created on 3.1.2017

@author: Samuli Rahkonen
'''

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license_file = f.read()

install_requires = ['Flask>=0.11.1',
                    'numpy>=1.11.2',
                    'matplotlib',
                    'xevacam>=0.0.1']

setup(name='xcamserver',
      version='0.0.1',
      description=readme,
      author='Samuli Rahkonen',
      author_email='samuli.rahkonen@jyu.fi',
      url='',
      install_requires=install_requires,
      packages=find_packages(),
      license=license_file,
      dependency_links=['git@yousource.it.jyu.fi:hsipython/xevacam.git@master']
      )
