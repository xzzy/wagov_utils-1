from setuptools import setup

setup(name='wagov_utils',
      version='1.02',
      description='DBCA WA GOV utils',
      url='https://github.com/dbca-wa/wagov_utils',
      author='Department of Biodiversity, Conservation and Attractions',
      author_email='asi@dbca.wa.gov.au',
      license='BSD',
      packages=['wagov_utils','wagov_utils.components'
                ],
      install_requires=[],
      include_package_data=True,
      zip_safe=False)
