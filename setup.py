"""Setup configuration for the media analyzer package."""

from setuptools import find_packages, setup

setup(
    name="media-analyzer",
    version="0.1.0",
    description="A Python package for analyzing audio and video content",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "SpeechRecognition>=3.10.0",
        "openai-whisper>=1.0.0",
        "pydub>=0.25.1",
        "nltk>=3.8.1",
        "spacy>=3.7.2",
        "tqdm>=4.66.1",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
            "pylint>=2.17.5",
            "pre-commit>=3.3.3",
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
)
