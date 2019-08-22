from setuptools import setup


setup(
        name='oda-workflows',
        version_format='{tag}.dev{commitcount}+{gitsha}',
        py_modules= ['workflows','service_exception'],
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
            'console_scripts': ['ew=workflows:evaluate_console'],
        },
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        long_description=open('README.md').read(),

        setup_requires=['setuptools-git-version'],
        )
