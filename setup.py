# Standard Library
from codecs import open
from os import path

from setuptools import find_packages
from setuptools import setup


here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'CHANGES.rst'), encoding='utf-8') as f:
    long_description += "\n" + f.read()

setup(
    name='pyramid_notebook',
    version='0.3.0',
    description='Embed IPython Notebook shell on your Pyramid website',
    long_description=long_description,
    url='https://github.com/websauna/pyramid_notebook',
    author='Mikko Ohtamaa',
    author_email='mikko@opensourcehacker.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Shells',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Pyramid',
        'Framework :: IPython',
    ],
    keywords='ipython setuptools development shell uwsgi',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    zip_safe=False,
    python_requires='>=3.5.2',
    include_package_data=True,
    install_requires=[
        "ipython[notebook]>=7.0.1",
        'daemonocle>=1.0.1',
        'PasteDeploy',
        'port-for',
        'pyramid',
        'sqlalchemy',
        'ws4py'
    ],
    extras_require={
        'dev': [
            'flake8',
            'flake8-isort',
            'zest.releaser[recommended]',
        ],
        'test': [
            'codecov',
            'flaky',
            'paste',
            'pyramid_jinja2',
            'pytest',
            'pytest-cov',
            'pytest-splinter',
            'selenium>3',
            'webtest',
        ],
        'uwsgi': [
            'uwsgi',
            'ws4py'
        ]
    },
    entry_points={
        "paste.app_factory": [
            'main = pyramid_notebook.demo:main'
        ]
    },
)
