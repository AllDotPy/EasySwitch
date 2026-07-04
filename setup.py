from setuptools import find_packages, setup

# LOADING DOCUMENTATION
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name = 'easyswitch',
    version = '0.1.2',
    packages = find_packages(),
    install_requires = [
        'aiohttp>=3.11.18',
        'phonenumbers>=9.0.5',
        'pydantic>=2.11.4',
        'python-dateutil>=2.9.0.post0',
        'python-dotenv>=1.1.0',
        'pyyaml>=6.0.2',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author = '#Einswilli',
    author_email = 'einswilligoeh@email.com',
    description = 'SwitchPay Python SDK for AllDotPy internal use. ',
    url = 'https://github.com/AllDotPy/EasySwitch.git',
)