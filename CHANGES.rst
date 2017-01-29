Changelog for pyramid_notebook
==============================

0.2.1 (2017-01-29)
------------------

- Fixed unnecessary "Enter token" prompt with the latest Jupyter Notebook versions


0.2 (2016-12-06)
----------------

- Upgraded to IPython 5.1 / Jupyter

- Better error messages in various situtations

- Add custom shutdown command by customizing IPython toolbar menu


0.1.11 (2016-04-18)
-------------------

- Upgrade to Daemonocle 1.0


0.1.10 (2016-01-31)
-------------------

- Allow easily override IPython Notebook current working directory.


0.1.9 (2016-01-31)
------------------

- Make it possible to override the default bootstrap scripts and greeting for ``make_startup()``


0.1.8 (2016-01-31)
------------------

- Adding ws4py as a dependency as it is required for uWSGI which is currently the only supported implementation


0.1.7 (2016-01-16)
------------------

- Fixed README reST syntax


0.1.6 (2016-01-16)
------------------

- Switch to xdaemonocle fork of Daemonocle library


0.1.5 (2016-01-07)
------------------

- Keep IPython Notebook in 3.x series now by setup.py pinnings, as IPython 4.0 is not supported yet


0.1.4 (2015-12-19)
------------------

- Fixed relative image links to absolute in README


0.1.3 (2015-12-19)
------------------

- Fixing MANIFEST.in and release issues due to setuptools_git not present


0.1.2 (2015-12-19)
------------------

- Fixed README markup

- Fixed broken drone.io integration which prevented tests to pass on CI

0.1.1 (2015-12-19)
------------------

- Fixed broken setup.py classifiers

0.1 (2015-12-19)
----------------

- Initial release.
