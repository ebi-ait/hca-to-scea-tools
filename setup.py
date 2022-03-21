import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()
install_requires = [line.rstrip() for line in (HERE / "requirements.txt").read_text().splitlines()]

setup(
    name="hca2scea",
    version="v0.1.1",
    description="A tool to assist in the automatic conversion of hca metadata to scea metadata MAGE-TAB files.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/ebi-ait/hca-to-scea-tools",
    author="Ami Day, Yusra Haider, Alegria Aclan, Javier Ferrer",
    author_email="ami@ebi.ac.uk, yhaider@ebi.ac.uk, aaclan@ebi.ac.uk, javier.f.g@um.es",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
    ],
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=install_requires,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "hca2scea=hca_to_scea.hca2scea:main",
        ]
    },
)

