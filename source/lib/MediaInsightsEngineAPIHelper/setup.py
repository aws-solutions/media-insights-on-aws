import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Media Insights Engine API Helper",
    version="0.0.1",
    author="Brandon Dold",
    author_email="redacted@example.com",
    description="Helper classes for interacting with the Media Insights Engine APIs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/awslabs/aws-media-insights-engine",
    packages=setuptools.find_packages(),
    install_requires=[
        'boto3',
        'requests',
        'requests_aws4auth'
      ],
    classifiers=[
        "Programming Language :: Python :: 3",
	"License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
)
