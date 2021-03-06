import os
from dataclasses import dataclass

import pytest

from notion.block.basic import Block
from notion.client import NotionClient


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


@dataclass
class NotionTestContext:
    client: NotionClient
    root_page: Block
    store: AttrDict


@pytest.fixture(scope="session", autouse=True)
def notion(_cache=[]):
    if _cache:
        return _cache[0]

    token_v2 = os.environ["NOTION_TOKEN_V2"].strip()
    page_url = os.environ["NOTION_PAGE_URL"].strip()

    client = NotionClient(token_v2=token_v2)
    page = client.get_block(page_url)
    store = AttrDict()

    if page is None:
        raise ValueError(f"No such page under url: {page_url}")

    notion = NotionTestContext(client, page, store)
    _cache.append(notion)

    yield notion

    clean_root_page(page)


def clean_root_page(page):
    for child in page.children:
        child.remove(permanently=True)

    page.refresh()


def assert_block_is_okay(notion, block, type: str, parent=None):
    parent = parent or notion.root_page

    assert block.id
    assert block.type == type
    assert block.alive is True
    assert block.is_alias is False
    assert block.parent == parent


def assert_block_attributes(block, **kwargs):
    for attr, value in kwargs.items():
        assert hasattr(block, attr)
        setattr(block, attr, value)

    block.refresh()

    for attr, value in kwargs.items():
        assert getattr(block, attr) == value
