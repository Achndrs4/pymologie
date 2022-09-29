from setuptools import setup, find_packages


setup(
    name='pymology',
    version='1.0',
    license='MIT',
    author="Ani Chandrashekhar",
    author_email='ani.chandrashekhar@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/gmyrianthous/example-publish-pypi',
    keywords='example project',
    install_requires=[
          'scikit-learn',
      ],
)
