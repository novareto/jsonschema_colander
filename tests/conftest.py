import json
import pytest
import pathlib
from functools import lru_cache


@lru_cache()
def load_file(name):
    return json.loads((pathlib.Path(__file__).parent / name).read_text())


@pytest.fixture(scope="session")
def product_schema(request):
    path = pathlib.Path(__file__).parent / 'product.json'
    with path.open('r') as fp:
        return json.load(fp)


@pytest.fixture(scope="session")
def person_schema(request):
    path = pathlib.Path(__file__).parent / 'person.json'
    with path.open('r') as fp:
        return json.load(fp)


@pytest.fixture(scope="session")
def address_schema(request):
    path = pathlib.Path(__file__).parent / 'address.json'
    with path.open('r') as fp:
        return json.load(fp)


@pytest.fixture(scope="session")
def geo_schema(request):
    path = pathlib.Path(__file__).parent / 'geo.json'
    with path.open('r') as fp:
        return json.load(fp)


@pytest.fixture(scope="session")
def refs_and_defs_schema(request):
    path = pathlib.Path(__file__).parent / 'refs_defs.json'
    with path.open('r') as fp:
        return json.load(fp)


@pytest.fixture(scope="session")
def extended_validation_schema(request):
    path = pathlib.Path(__file__).parent / 'extended_validation.json'
    with path.open('r') as fp:
        return json.load(fp)


@pytest.fixture(scope="session")
def extended_validation_schema_all_of(request):
    path = pathlib.Path(__file__).parent / 'extended_validation_allOf.json'
    with path.open('r') as fp:
        return json.load(fp)
