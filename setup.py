from setuptools import setup, find_packages
import os

version = '2.0dev'

selenium_require = [
    'selenium'
]
tests_require = [
    'selenium',
    'pytest',
]

setup(name='infrae.testbrowser',
      version=version,
      description="Sane functionnal test browser for WSGI applications",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='test wsgi application functional',
      author='Infrae',
      author_email='info@infrae.com',
      url='http://infrae.com/products/silva',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['ez_setup']),
      namespace_packages=['infrae',],
      include_package_data=True,
      zip_safe=False,
      test_suite='infrae.testbrowser',
      install_requires=[
        'setuptools',
        'lxml',
        'zope.interface',
        ],
      extras_require = {'selenium': selenium_require,
                        'test': tests_require},
      tests_require = tests_require,
      )
