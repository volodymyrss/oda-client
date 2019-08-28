from setuptools import setup


setup(
        name='oda',
        version_format='{tag}.dev{commitcount}+{gitsha}',
        url="http://odahub.io",
        packages = ['oda'],
        package_data     = {
            "": [
                "*.txt",
                "*.md",
                "*.rst",
                "*.py"
                ]
            },
        entry_points = {
            'console_scripts': ['ew=oda.router:evaluate_console'],
        },
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        long_description=open('README.md').read(),

        setup_requires=['setuptools-git-version'],
        )
