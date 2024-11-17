from setuptools import setup, find_packages

setup(
    name="berluf_selen_2_ctrl",
    version="0.2.3",
    description="Package for controlling Berluf Selen 2 recuperator.",
    url="https://github.com/3p3v/berluf_selen_2_ctrl",
    author="Adam Golecki",
    author_email="adam@golecki.pl",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "pymodbus_3p3v==3.7.4.5",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9.0",
)
