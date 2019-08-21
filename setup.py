from setuptools import setup, find_packages

INSTALL_REQUIRES = []
with open("requirements.txt", "r", encoding="utf-8") as f:
    INSTALL_REQUIRES = list(i.rstrip() for i in f.readlines())

EXTRA_REQUIRE = []
with open("requirements.dev.txt", "r", encoding="utf-8") as f:
    EXTRA_REQUIRE = list(i.rstrip() for i in f.readlines())

setup(
    name="exoscale",
    packages=find_packages(),
    version="0.1.0",
    license="ISC",
    author="Exoscale",
    platforms="any",
    classifiers=(
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ),
    install_requires=INSTALL_REQUIRES,
    extra_require=EXTRA_REQUIRE,
    tests_require=["pytest>=5.0.0"],
)
