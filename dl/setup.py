import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='downloader',
    version='1.0',
    author='ZSAIm',
    author_email='405935987@163.com',
    description='not bad downloader',
    long_description=long_description,
    url='https://github.com/ZSAIm/downloader',
	install_requires=[],
    packages=setuptools.find_packages(),
    classifiers=(

        'Programming Language :: Python :: 2.7',


    ),
    zip_safe=False
)
