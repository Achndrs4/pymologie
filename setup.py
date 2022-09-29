from setuptools import setup, find_packages

setup(
    name='pymologie',
    version='1.0',
    license='MIT',
    author="Ani Chandrashekhar",
    author_email='ani.chandrashekhar@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/Achndrs4/pymologie',
    keywords='pymologie, etymologie, wortherkunft, wortherkünfte',
)
