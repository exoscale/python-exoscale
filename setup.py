from setuptools import setup, find_packages

INSTALL_REQUIRES = []
with open("requirements.txt", "r", encoding="utf-8") as f:
    INSTALL_REQUIRES = list(i.rstrip() for i in f.readlines())

EXTRA_REQUIRE = []
with open("requirements.dev.txt", "r", encoding="utf-8") as f:
    EXTRA_REQUIRE = list(i.rstrip() for i in f.readlines())

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="exoscale",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests",)),
    version="0.5.1",
    license="ISC",
    url="https://github.com/exoscale/python-exoscale",
    author="Exoscale",
    author_email="contact@exoscale.com",
    platforms="any",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6",
    install_requires=INSTALL_REQUIRES,
    extra_require=EXTRA_REQUIRE,
    tests_require=["pytest>=5.0.0"],
    include_package_data=True,
)
