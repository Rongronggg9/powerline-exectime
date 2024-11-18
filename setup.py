# vim:fileencoding=utf-8:noet

from setuptools import setup, find_packages

setup(
    name='powerline-exectime',
    description='A Powerline segment to show the execution time of the last command',
    version='0.5.0',
    keywords='powerline terminal console shell bash',
    license='MIT',
    author='Rongrong',
    author_email='i@rong.moe',
    url='https://github.com/Rongronggg9/powerline-exectime',
    packages=['powerline_exectime'],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Terminals'
    ],
    include_package_data=True,
    zip_safe=False,
)
