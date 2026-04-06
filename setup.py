"""OpenClaw-Medical-Harness setup."""

from setuptools import setup, find_packages

setup(
    name="openclaw-medical-harness",
    version="0.1.0",
    description="Medical AI Agent Orchestration Framework for OpenClaw — Built on Harness Theory",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="MoKangMedical",
    url="https://github.com/MoKangMedical/openclaw-medical-harness",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.0.0",
        "httpx>=0.27.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "crewai": ["crewai[tools]>=0.28.0"],
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.23",
            "ruff>=0.3",
            "mypy>=1.8",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Framework :: OpenClaw",
    ],
    keywords="openclaw medical ai harness agent orchestration diagnosis drug-discovery",
)
