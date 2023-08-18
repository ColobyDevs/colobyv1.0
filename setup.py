from setuptools import setup, find_packages

setup(
    name='file-transfer-tool',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Django',  # Add any other dependencies your package needs
    ],
    entry_points={
        'console_scripts': [
            'file-transfer = commands.command:main',
        ],
    },
)
