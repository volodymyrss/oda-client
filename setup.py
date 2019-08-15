from setuptools import setup


setup(
        name='integral-client',
        version='1.0.0',
        py_modules= ['odaw','service_exception'],
        url="http://odahub.io",
        package_data     = {
            "": [
                "*.txt",
                "*.md",
                "*.rst",
                "*.py"
                ]
            },
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        long_description=open('README.md').read(),
        )
