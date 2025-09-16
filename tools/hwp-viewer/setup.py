from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hwp-viewer",
    version="0.1.0",
    author="Your Name",
    author_email="your-email@example.com",
    description="A versatile HWP (Hangul Word Processor) file viewer and converter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hwp-viewer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Text Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "olefile>=0.46",
        "pyhwp>=0.1b12",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "click>=8.0.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.0.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "converter": [
            "pypandoc>=1.11",
            "reportlab>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hwp-viewer=cli.hwp_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)