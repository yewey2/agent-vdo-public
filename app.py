import streamlit as st
import os

logo_path = None
if os.path.exists("./images/logo.png"):
    logo_path = "./images/logo.png"
elif os.path.exists("/agent_vdo_mini/images/logo.png"):
    logo_path = "/agent_vdo_mini/images/logo.png"
else:
    print(os.getcwd())
    print(os.path.join(os.getcwd(), "../../images/logo.png"))



st.set_page_config(
    page_title="Home",
    page_icon=logo_path or "🏠",
    # layout="wide",
    layout="centered",
    initial_sidebar_state="collapsed",
    # initial_sidebar_state="expanded",
)

if logo_path:
    st.logo(logo_path)

from st_utils import switch_page, go_to_homepage
from streamlit.source_util import get_pages

def standardize_name(name: str) -> str:
    return name.lower().replace("_", " ")

pages = get_pages(os.path.basename(__file__))

page_names = [standardize_name(config["page_name"]) for config in pages.values()]

app_name = "Team Agent VDO"
powered_by = "Powered by Agent VDO"
left,right = st.columns([1,4])
left.image(logo_path)
right.title(f"{app_name}")
right.write(f"### {powered_by}")
st.write("Hello! Please select the app that you would like to use below.")


# for page in pages.values():
#     with cols[col_i]:
#         if (
#             page["page_name"] in ("app", ) or # default pages
#             "test" in page["page_name"].lower() # test pages, not live
#             ):
#             continue
#         if st.button(f'{page["page_name"].replace("_", " ")}', use_container_width=True):
#             switch_page(page['page_name'])
#     col_i += 1
#     col_i %= 3

## First 3 EQ-5D Pages
st.write("## EQ-5D")
_, *cols, _ = st.columns([1,3,3,3,1])
# col_i = 1 ## start from center
col_i = 0 ## start from left
for page in pages.values():
    if page["page_name"] in ("app", ) or "test" in page["page_name"].lower():
        continue
    if page["page_name"] in ("EQ-5D_Extraction", "EQ-5D_Visualization", "EQ-5D_Insights"):
        with cols[col_i]:
            if st.button(f'{page["page_name"].replace("_", " ")}', use_container_width=True):
                switch_page(page['page_name'])
        col_i += 1
        col_i %= 3

## Next 3 EORTC Pages
st.write("---")
st.write("## EORTC")
_, *cols, _ = st.columns([1,3,3,3,1])
# col_i = 1 ## start from center
col_i = 0 ## start from left
for page in pages.values():
    if page["page_name"] in ("app", ) or "test" in page["page_name"].lower():
        continue
    if page["page_name"] in ("EORTC_Extraction", "EORTC_Visualization", "EORTC_Insights"):
        with cols[col_i]:
            if st.button(f'{page["page_name"].replace("_", " ")}', use_container_width=True):
                switch_page(page['page_name'])
        col_i += 1
        col_i %= 3        




st.container(height=500, border=False)

st.session_state.update({
    "input_data": None,
    "output_data": None, 
    "selected_case": None,
    "display_output": None,
})