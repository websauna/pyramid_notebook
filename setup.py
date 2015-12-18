# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'CHANGES.rst'), encoding='utf-8') as f:
    long_description += "\n" + f.read()


setup(
    name='pyramid_notebook',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.4',

    description='Embed IPython Notebook shell on your Pyramid website',
    long_description=long_description,

    # The project's main homepage.
    url='https://bitbucket.org/miohtama/pyramid_notebook ',

    # Author details
    author='Mikko Ohtamaa',
    author_email='mikko@opensourcehacker.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Shells',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Framework :: Pyramid',
        'Framework :: IPython',
    ],

    # What does your project relate to?
    keywords='ipython setuptools development shell uwsgi',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    include_package_data=True,

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['port-for', "ipython[notebook]", 'pyramid', 'daemonocle'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['codecov', 'pytest', 'pyramid_jinja2', 'paste', "pytest-splinter", "webtest", "pytest-cov"],
        'uwsgi': ['uwsgi', 'PasteDeploy', 'ws4py']
    },

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        "paste.app_factory": [
            'main = pyramid_notebook.demo:main'
        ]
    },
)
