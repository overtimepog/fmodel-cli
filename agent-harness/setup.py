from setuptools import setup, find_packages

setup(
    name="fmodel-cli",
    version="0.1.0",
    description="CLI for FModel — agent-native UE4/UE5 game asset browser. Parse PAK files, inspect .uasset Blueprints, extract game content from the terminal.",
    author="truen",
    url="https://github.com/overtimepog/fmodel-cli",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
        "prompt_toolkit>=3.0",
    ],
    entry_points={
        "console_scripts": [
            "fmodel=fmodel_cli.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
