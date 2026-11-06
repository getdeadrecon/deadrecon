from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()



def read_requirements(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = (line.split("#", 1)[0].strip() for line in f)
        return [line for line in lines if line]


setup(
    name="deadrecon",
    version="1.31.2",
    description="The OPSEC-native OSINT framework: stealth egress, one-click Tor, and an honest per-scan report of what you bled.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="the-clipper",
    url="https://github.com/getdeadrecon/deadrecon",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "server": read_requirements("requirements-server.txt"),
    },
    entry_points={
        "console_scripts": [
            "deadrecon=deadrecon.cli:main",
            "drecon=deadrecon.cli:main",
            # Old commands, kept so existing scripts keep working
            "phantomsignal=deadrecon.cli:main",
            "psig=deadrecon.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: System :: Networking :: Monitoring",
    ],
    keywords="osint opsec tor reconnaissance recon attack-surface-management security pentest deadrecon phantomsignal",
    project_urls={
        "Homepage": "https://deadrecon.sh",
        "Documentation": "https://github.com/getdeadrecon/deadrecon/blob/main/docs/USAGE.md",
        "Changelog": "https://github.com/getdeadrecon/deadrecon/blob/main/CHANGELOG.md",
        "Releases": "https://github.com/getdeadrecon/deadrecon/releases",
        "Bug Reports": "https://github.com/getdeadrecon/deadrecon/issues",
        "Source": "https://github.com/getdeadrecon/deadrecon",
    },
)
