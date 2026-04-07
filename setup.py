"""Setup configuration for OpenClaw-Medical-Harness."""

from setuptools import setup, find_packages

setup(
    name="openclaw-medical-harness",
    version="0.1.0",
    description="Medical AI Agent Orchestration Framework for OpenClaw — Built on Harness Theory",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="MoKangMedical",
    author_email="mokangmedical@example.com",
    url="https://github.com/MoKangMedical/openclaw-medical-harness",
    license="MIT",
    packages=find_packages(include=["openclaw_medical_harness", "openclaw_medical_harness.*"]),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "openclaw": ["openclaw>=2026.4.0"],
        "crewai": ["crewai>=0.28.0"],
        "all": ["openclaw>=2026.4.0", "crewai>=0.28.0"],
        "server": ["fastapi>=0.104.0", "uvicorn>=0.24.0"],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-asyncio>=0.21",
            "mypy>=1.0",
            "ruff>=0.1.0",
            "pre-commit>=3.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="medical ai agent harness openclaw diagnosis drug-discovery health-management",
    project_urls={
        "Documentation": "https://mokangmedical.github.io/openclaw-medical-harness",
        "Source": "https://github.com/MoKangMedical/openclaw-medical-harness",
        "Issues": "https://github.com/MoKangMedical/openclaw-medical-harness/issues",
    },
)
