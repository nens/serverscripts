from setuptools import setup

version = '0.6'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    # This shall remain empty upon pain of death.
    #
    # We're being installed on servers and we don't want to pollute the
    # system-wide python lib directory with dependencies.
    ],

tests_require = [
    'coverage',
    'mock',
    'nose',
    ]

setup(name='serverscripts',
      version=version,
      description="Python scripts for sysadmin tasks on every linux server",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords=[],
      author='Reinout van Rees',
      author_email='reinout.vanrees@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['serverscripts'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
              'cifsfixer = serverscripts.cifsfixer:main',
              'checkout-info = serverscripts.checkouts:main',
          ]},
      )
