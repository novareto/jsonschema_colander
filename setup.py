from setuptools import setup


setup(
    name='jsonschema_colander',
    install_requires=[
        'colander>=1.8',
        'jsonschema',
        'unflatten'
    ],
    extras_require={
        'test': [
            'pytest>=3',
            'PyHamcrest'
        ]
    }
)
