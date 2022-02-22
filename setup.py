import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="hca-to-scea",
    version="1.0.0",
    description="A tool to convert an HCA metadata spreadsheet to SCEA MAGE-TAB metadata files.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/ebi-ait/hca-to-scea-tools",
    author="Ami Day, Javier Ferrer, Yusra Haider, Alegria Aclan",
    author_email="ami@ebi.ac.uk, javier.f.g@um.es, yhaider@ebi.ac.uk, aaclan@ebi.ac.uk",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["hca-to-scea"],
    include_package_data=True,
    install_requires=["glob","requests","numpy","pandas","elementpath","contextlib2"],
    entry_points={
        "console_scripts": [
            "hca-to-scea=hca2scea.__main__:main",
        ]
    },
)

