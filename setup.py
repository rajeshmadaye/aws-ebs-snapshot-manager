import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='snapshotManager',
    version='0.1',
    scripts=['snapshotManager.py'] ,
    author="Rajesh Madaye",
    author_email="rajeshmadaye@yahoo.com",
    description="AWS Snapshot management package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rajeshmadaye/aws-snapshot-mgr.git",
    packages=setuptools.find_packages(),
    install_requires=['tendo'],
    classifiers=[
       "Programming Language :: Python :: 3",
       "License :: OSI Approved :: MIT License",
       "Operating System :: OS Independent",
    ],
 )