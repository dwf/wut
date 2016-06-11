from setuptools import setup


setup(name='wut',
      version='0.0.1',
      description='An urwid-based Wunderlist client.',
      url='http://github.com/dwf/wut',
      author='David Warde-Farley',
      author_email='dwf@dwf.name',
      license='MIT',
      packages=['wut'],
      scripts=['scripts/wut'],
      zip_safe=False)
