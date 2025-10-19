from setuptools import setup, find_packages

setup(
    name="miso_engine",
    version="0.1.0",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        "langchain",
        "langchain-core",
        "langchain-openai",
        "pytest",
        "celery",
        "redis",
        "chromadb",
        "sentence-transformers",
        "setuptools"
    ],
)
