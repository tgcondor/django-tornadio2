import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django_tornadio2",
    version = "0.1.0",
    author = "LetoLab Ltd",
    author_email = "team@letolab.com",
    description = ("Drop-in replacemenet for runserver command to run Django on Tornado with Tornadio2"),
    long_description=read('README.md'),
    license = "Apache License 2.0",
    keywords = "web development websockets",
    url = "https://github.com/letolab/django-tornadio2",
    packages=find_packages(),
    include_package_data=True,
    requires=[
        'tornado',
        'tornadio2',
    ],
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 3 - Alpha",
    ],
)

