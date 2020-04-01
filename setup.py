import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("VERSION", "r") as version_file:
    version = version_file.read().strip()
with open("requirements.txt", "r") as requirements_file:
    install_requires = requirements_file.read().splitlines()

setuptools.setup(
    name="ircstates",
    version=version,
    author="jesopo",
    author_email="pip@jesopo.uk",
    description="IRC client session state parsing library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jesopo/ircstates",
    packages=setuptools.find_packages(),
    package_data={"ircstates": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Communications :: Chat :: Internet Relay Chat"
    ],
    python_requires='>=3.6',
    install_requires=install_requires
)
