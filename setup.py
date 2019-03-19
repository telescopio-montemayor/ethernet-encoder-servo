import os
from setuptools import find_packages, setup

from ethernet_servo import __version__


with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ethernet-encoder-servo',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'attrs',
        'cpppo==3.9.5',
        'greenery==2.1',
        'ipaddress==1.0.18',
        'astropy',
        'pyserial',
        'flask',
        'flask-environments',
        'flask-socketio',
        'flask-restplus',
        'flask-cors',
        'eventlet',
    ],
    license='AGPL-3.0',
    description='Networked servo controller around CIP encoders and step/direction motors for use with a telescope.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/telescopio-montemayor/ethernet-encoder-servo',
    author='Adrián Pardini',
    author_email='github@tangopardo.com.ar',
    entry_points={
        'console_scripts': [
            'ethernet-servo=ethernet_servo:main'
        ]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Telecommunications Industry',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Communications',
        'Topic :: Education',
        'Topic :: Scientific/Engineering :: Astronomy'
    ],
    keywords='astronomy, telescope, industrial, CIP, encoder',
)
