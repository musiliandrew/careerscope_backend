from setuptools import setup, find_packages

setup(
    name="careerscope-shared",
    version="0.1.0",
    description="Shared AI SDK, Contracts, and Configuration for CareerScope",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-ai>=2.0.0",
        "python-dotenv",
        "pyyaml" # For frontmatter parsing in prompt registry
    ],
)
