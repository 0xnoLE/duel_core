from setuptools import setup, find_packages

setup(
    name="duelsim",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "duelsim": ["config/*.json"],
    },
    description="A turn-based duel simulation engine",
    author="Your Name",
    author_email="olmniverse@gmail.com",
    url="https://github.com/0xnoLE/duel_core",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.6",
) 