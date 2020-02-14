import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Media Insights Engine Lambda Helper",
    version="0.0.3",
    author="Brandon Dold",
    author_email="brandold@amazon.com",
    description="Helper classes for developing Media Insights Engine Lambda Functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://code.amazon.com/packages/MediaInsightsEngine",
    packages=setuptools.find_packages(),
    install_requires=[
        'boto3',
        'urllib3'
      ],
    classifiers=[
        "Programming Language :: Python :: 3",
	"License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
)
