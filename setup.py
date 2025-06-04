# This file is kept for backwards compatibility with setuptools
# but the project now uses Poetry for dependency management and packaging.
# See pyproject.toml for the actual build configuration.

from setuptools import setup, find_packages

setup(
    name="fastapi-profiler-lite",
    version="0.3.2",
    description="A lightweight performance profiler for FastAPI applications",
    author="Alexander Lind",
    author_email="al91liwo@gmail.com",
    url="https://github.com/al91liwo/fastapi-profiler",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "fastapi_profiler": [
            "static/css/*.css",
            "static/js/*.js",
            "static/templates/*.html",
        ],
    },
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.68.0",
        "starlette>=0.14.2",
        "jinja2>=3.1.2",
        "sqlparse>=0.4.0",
        "sqlalchemy>=1.4.0",
        "fastapi-profiler-rust>=0.3.2)"
    ],
    extras_require={
        "standard": ["uvicorn>=0.14.0"],
        "dev": ["pytest>=6.0.0", "ruff>=0.1.0", "uvicorn>=0.14.0", "httpx>=0.24.0"],
        "sqlalchemy": ["sqlalchemy>=1.4.0", "sqlparse>=0.4.0"],
        "all": ["uvicorn>=0.14.0", "sqlalchemy>=1.4.0", "sqlparse>=0.4.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
