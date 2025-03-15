import streamlit as st
import os

## Streamlit Configs and default headers
logo_path = None
if os.path.exists("./images/logo.png"):
    logo_path = "./images/logo.png"
    folder_stem = ""
elif os.path.exists("/agent_vdo_mini/images/logo.png"):
    logo_path = "/agent_vdo_mini/images/logo.png"
    folder_stem = "/agent_vdo_mini/"
st.set_page_config(
    page_title="EQ-5D Extraction",
    page_icon=logo_path,
    # layout="centered",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

if st.button("🏠 Go to homepage"):
    go_to_homepage()

title = "Agent VDO: Extraction of PROMs"
if logo_path:
    st.logo(logo_path)
    left, right = st.columns([1, 11])
    left.image(logo_path)
    right.title(title)
else: 
    st.title(title)

from functions.idea_1 import *
from functions.idea_1_annotate import annotateQuery
from copy import deepcopy
import markdown

## Imports
import pandas as pd
import json

## Pre-load data
## Key-value pairs for Case Number and JSON file

st.session_state.input_mapping_dict = {
    "Synthetic Case 1 (Admission Notes)": "case_1_synthetic_firstnote.docx",
    "Synthetic Case 5 (Admission Notes)": "case_5_synthetic_firstnote.docx",
    "Synthetic Case 6 (Admission Notes)": "case_6_synthetic_firstnote.docx",
    "Synthetic Case 1 (Pre-Discharge Notes)": "case_1_synthetic_lastnote.docx",
    "Synthetic Case 5 (Pre-Discharge Notes)": "case_5_synthetic_lastnote.docx",
    "Synthetic Case 6 (Pre-Discharge Notes)": "case_6_synthetic_lastnote.docx",
}

st.session_state.output_mapping_dict = {
    "Synthetic Case 1 (Admission Notes)": "syn_case_1_result.json",
    "Synthetic Case 5 (Admission Notes)": "syn_case_5_result.json",
    "Synthetic Case 6 (Admission Notes)": "syn_case_6_result.json",
    "Synthetic Case 1 (Pre-Discharge Notes)": "syn_case_1_pre_discharge_result.json",
    "Synthetic Case 5 (Pre-Discharge Notes)": "syn_case_5_pre_discharge_result.json",
    "Synthetic Case 6 (Pre-Discharge Notes)": "syn_case_6_pre_discharge_result.json",
}

TO_SHOW_CASES = [
    "Synthetic Case 1 (Admission Notes)", 
    "Synthetic Case 5 (Admission Notes)", 
    "Synthetic Case 6 (Admission Notes)", 
    "Synthetic Case 1 (Pre-Discharge Notes)", 
    "Synthetic Case 5 (Pre-Discharge Notes)", 
    "Synthetic Case 6 (Pre-Discharge Notes)",
]

## Streamlit UI

if st.session_state.get("input_data") is None:
    st.session_state.input_data = {}
    for key, value in st.session_state.input_mapping_dict.items():
        if key not in TO_SHOW_CASES:
            continue
        st.session_state.input_data[key] = get_text_from_docx(f"{folder_stem}eq5d/{value}")

input_mapping_dict = st.session_state.input_mapping_dict

output_mapping_dict = st.session_state.output_mapping_dict

if st.session_state.get("output_data") is None:
    st.session_state.output_data = {}
    for key, value in st.session_state.output_mapping_dict.items():
        if key not in TO_SHOW_CASES:
            continue
        if not os.path.exists(f"{folder_stem}eq5d/{value}"):
            result = extract_prom_prem_from_docx(f"{folder_stem}eq5d/{st.session_state.input_mapping_dict[key]}", False)
            with open(f"{folder_stem}eq5d/{value}", 'w') as file:
                result = extract_eval_json(result)
                json.dump(result, file, indent=4)
        with open(f"{folder_stem}eq5d/{value}", 'r') as file:
            st.session_state.output_data[key] = json.load(file)

input_data, output_data = st.session_state.input_data, st.session_state.output_data


if st.session_state.get("selected_case") is None:
    st.session_state.selected_case = None
col1, col2 = st.columns(2, gap="large")
with col1:
    st.session_state.case_notes_input_old = st.session_state.get("case_notes_input")
    st.write("# Input Data")
    st.write("### Select an example case.")
    selected_case = st.selectbox("Select Case Number", list(input_data.keys()), index=None)
    if selected_case != st.session_state.selected_case:
        st.session_state.selected_case = selected_case
        st.session_state.case_notes_input = None
    selected_case_text = input_data[selected_case] if selected_case is not None else ""
    st.write("### Or, enter your own text:")
    st.warning("Note: Do not enter any sensitive information, as the data will be sent to the server for processing.")
    with st.form("case_notes_form"):
        if st.session_state.get("case_notes_input") is None:
            st.session_state.case_notes_input = selected_case_text
            st.rerun()
        case_notes_input = st.text_area("Case Notes", key="case_notes_input", value=st.session_state.case_notes_input, height=400, placeholder="Enter your case notes here.", label_visibility="collapsed")
        with st.columns([3,1])[1]:
            form_submit_button = st.form_submit_button("Extract EQ-5D", type="primary", use_container_width=True)
    
with col2:
    st.write("# Output Data")
    ## check if case note inputs changed
    # if st.session_state.case_notes_input_old != st.session_state.case_notes_input or st.session_state.get("display_output", None) is None:
    if True:
        if case_notes_input in input_data.values():
            display_output = output_data[selected_case]
        elif selected_case is None:
            display_output = None
        else:
            display_output = extract_prom_prem_from_text(case_notes_input, False)
            display_output = extract_eval_json(display_output)

        st.session_state.display_output = display_output
    else:
        display_output = st.session_state.get("display_output")
    # st.json(display_output)
    st.write("### Extracted Data")
    if not st.session_state.get("show_extracted_data"):
        st.session_state.show_extracted_data = True
    def toggle_show_extracted_data(*args, **kwargs):
        st.session_state.show_extracted_data = not st.session_state.show_extracted_data
    with st.expander(
        "Click to show/hide extracted data" if not st.session_state.show_extracted_data else "Click to show/hide extracted data", 
        expanded=st.session_state.show_extracted_data, 
        # on_click=toggle_show_extracted_data,
        ):
        # st.write(f"```json\n{json.dumps(display_output, indent=2)}\n```")
        # display_output2 = deepcopy(display_output)
        # for d in display_output2.values():
        #     d['supporting_statements'] = "\n".join(d['supporting_statements'])

        # df = pd.DataFrame.from_dict(display_output2, orient='index')
        if display_output:
            df = pd.DataFrame.from_dict(display_output, orient='index')
        
            # Rename the index to match the desired row names
            df.index = ["Mobility", "Self Care", "Usual Activities", "Pain / Discomfort", "Anxiety / Depression"]

            # Select and rename the columns
            df = df[["final_score", "supporting_statements"]]
            df.columns = ["Final Score", "Supporting Statements From Case Notes"]
            st.dataframe(df)
        else:
            st.write("No data extracted.")
        
        
    if display_output:
    ## Show the highlights
        st.write("### Highlighted Case Notes")
        annotation_output = {"answers": []}
        for key, value in display_output.items():
            for i, statement in enumerate(value["supporting_statements"]):
                annotation_output["answers"].append({
                    "cited_sentence": statement,
                    "category": key,
                    "score": value["final_score"]
                })
        annotations_input = markdown.markdown(case_notes_input)
        
        # Define the colormap
        colormap = {
            "mobility": "#f08080",
            "self_care": "#e0a050",
            "usual_activities": "#f0f090",
            "pain_discomfort": "#80f080",
            "anxiety_depression": "#a0a0f0",
        }
        # Define the tagging map
        taggingmap = {
            "mobility": "MOB",
            "self_care": "S.C",
            "usual_activities": "U.A",
            "pain_discomfort": "P/D",
            "anxiety_depression": "A/D",
        }
        categorymap = {
            "mobility": "Mobility",
            "self_care": "Self Care",
            "usual_activities": "Usual Activities",
            "pain_discomfort": "Pain / Discomfort",
            "anxiety_depression": "Anxiety / Depression",
        }

        # Function to wrap the sentence with HTML span and color
        def wrap_sentence_with_color(sentence, category, score):
            total_score = 5
            color = colormap[category]
            tagging = taggingmap[category]
            return f'<span style="background-color: #c0c0c0; border-radius: 0.5rem; padding:0.2rem 0.5rem 0.1rem;color:black;line-height: 1rem;" title="{categorymap[category]}">{sentence} <span style="background-color:{color};color:black;border-radius:0.5rem; padding: 0.1rem 0.5rem; margin:0.1rem 0.1rem; font-size:0.8rem;line-height: 1rem;"><strong>{tagging}</strong>: {score}/{total_score}</span></span>'

        # Initialize an offset to keep track of the changes in the HTML string length
        offset = 0

        # Iterate over each cited sentence
        for answer in annotation_output['answers']:
            cited_sentence = answer["cited_sentence"]
            category = answer["category"]
            score = answer["score"]

            # Lowercase the cited sentence for case-insensitive search
            cited_sentence_lower = cited_sentence.lower()

            # Search for the cited sentence in the user input
            start = annotations_input.lower().find(cited_sentence_lower)

            if start != -1:
                end = start + len(cited_sentence)

                # Wrap the cited sentence with HTML span and color
                wrapped_sentence = wrap_sentence_with_color(cited_sentence, category, score)

                # Update the HTML with the offset
                annotations_input = annotations_input[:start + offset] + wrapped_sentence + annotations_input[end + offset:]

                # Update the tokens list
                # tokens.append({
                #     'entity': cited_sentence,
                #     'score': float(score),
                #     'index': len(tokens) + 1,
                #     'word': cited_sentence,
                #     'start': start + offset,
                #     'end': end + offset,
                #     "label": f"{category} : {score}/5"
                # })
        
        ## show the legend
        with st.expander("Legend (click to show/hide)", expanded=False):
            st.markdown(
                """
                <div style='background-color: #c0c0c0; border-radius: 0.5rem; padding: 0.2rem 0.5rem; color: black; margin: 0.5rem 0; display: flex; flex-wrap: wrap; align-items: center;gap: 0.2rem;'>
                """
                +
                # <span style='background-color: #f08080; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>MOB</strong>: Mobility</span>
                # <span style='background-color: #e0a050; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>S.C</strong>: Self Care</span>
                # <span style='background-color: #f0f090; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>U.A</strong>: Usual Activities</span>
                # <span style='background-color: #80f080; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>P/D</strong>: Pain / Discomfort</span>
                # <span style='background-color: #a0a0f0; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>A/D</strong>: Anxiety / Depression</span>
                "\n".join([f'<span style="background-color:{color};margin:1rem;border-radius:0.5rem; padding: 0.1rem 0.5rem; margin:0.1rem 0;"><strong>{taggingmap[category]}</strong>: {categorymap[category]}</span>' for category, color in colormap.items()])
                +
                """
                </div>
                """,
                unsafe_allow_html=True
            )
        with st.container(height=500, border=True):
            st.markdown(annotations_input, unsafe_allow_html=True)

