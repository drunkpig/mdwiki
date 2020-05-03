import setuptools

with open("README.MD", "r", encoding='utf-8') as fh:
    long_description = fh.read()

with open("requirements.txt", 'r', encoding='utf-8') as f:
    dependencies = f.readlines()

setuptools.setup(
    name="mdwiki",
    version="0.1.0",
    author="niceMachine",
    author_email="xuchaoo@gmail.com",
    description="zero config static blog builder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/drunkpig/mdwiki",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=['mdwiki/bin/mdpub'],
    # entry_points={
    #       'console_scripts': ['mdpub=mdwiki/bin/mdpub'],
    #   },
    install_requires=dependencies,

    python_requires='>=3.7',
)