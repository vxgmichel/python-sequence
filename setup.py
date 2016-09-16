#!/usr/bin/env python

from setuptools import setup, find_packages
from setuptools import Command

# Build and update pyqt resources
import sequence.resource.pyqt
del sequence


class UploadGhPages(Command):
    '''Command to update build and upload sphinx doc to github.'''
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Import fabric
        try:
            from fabric.api import local
        # Import subprocess
        except ImportError:
            from subprocess import call
            from functools import partial
            local = partial(call, shell=True)
        # Create gh-pages branch
        local('git checkout --orphan gh-pages ')
        # Unstage all
        local('rm .git/index')
        # Build doc
        local('python setup.py build_sphinx')
        # No jekyll file
        local('touch .nojekyll')
        local('git add .nojekyll')
        # Add Readme
        local('git add README.md')
        # Add html content
        local('git add docs/build/html/* -f ')
        # Move html content
        local('git mv docs/build/html/* ./ ')
        # Git commit
        local('git commit -m "build sphinx" ')
        # Git push
        local('git push --set-upstream origin gh-pages -f ')
        # Back to master
        local('git checkout master -f ')
        # Delete branch
        local('git branch -D gh-pages ')


setup(
    name='python-sequence',
    version='0.1.0',
    description='Package for sequence edition and execution.',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.png', '*.ui', '*.qrc']},
    cmdclass={'upload_gh_pages': UploadGhPages},
    entry_points={
        'console_scripts': [
            'sequence-console = sequence.console:main'],
        'gui_scripts': [
            'sequence-runner = sequence.runner:main',
            'sequence-editor = sequence.editor:main']},
)
