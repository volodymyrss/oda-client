from setuptools import setup


setup(
        name='oda-workflows',
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
        entry_points = {
            'console_scripts': ['ew=odaw:evaluate_console'],
        },
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        long_description=open('README.md').read(),
        )
