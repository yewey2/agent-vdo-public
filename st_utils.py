import streamlit as st
import os
from streamlit.runtime.scriptrunner import RerunData
from streamlit.runtime.scriptrunner.script_runner import RerunException
from streamlit.source_util import get_pages

def go_to_homepage(homepage_name="app"):
    pages = get_pages(os.path.basename(__file__))
    page_name = homepage_name
    for page_hash, config in pages.items():
        if (config["page_name"]) == page_name:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=page_name,
                )
            )

    raise ValueError(f"Could not find page {page_name}.")


def switch_page(page_name: str):
    def standardize_name(name: str) -> str:
        return name.lower().replace("_", " ")
    
    page_name = standardize_name(page_name)
    pages = get_pages(os.path.basename(__file__))

    for page_hash, config in pages.items():
        if standardize_name(config["page_name"]) == page_name:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=page_name,
                )
            )
    page_names = [standardize_name(config["page_name"]) for config in pages.values()]

    raise ValueError(f"Could not find page {page_name}. Must be one of {page_names}")

