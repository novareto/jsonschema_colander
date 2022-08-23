from setuptools import setup


setup(
    name='jsonschema_colander',
    install_requires=[
        'colander>=1.8',
        'jsonschema',
        'jsonref'
    ],
    extras_require={
        'test': [
            'pytest>=3',
            'PyHamcrest'
        ]
    }
)
