from setuptools import setup

setup(
    name='colup',
    version='0.1',
    scripts=['file_uploader.py'],
    install_requires=[
        'requests', 
          # Other dependencies can come here as time goes on
    ],
)
