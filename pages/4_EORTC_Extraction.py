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
    page_title="EORTC Extraction",
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
import random

## Pre-load data
## Key-value pairs for Case Number and JSON file

st.session_state.input_mapping_dict = {
    "Live Case 1 Admission Case Notes": "eortc_case_1_synthetic.docx",
    "Live Case 1 Pre-Discharge Case Notes": "eortc_case_1_synthetic_predischarge.docx",
}

st.session_state.output_mapping_dict = {
    "Live Case 1 Admission Case Notes": "eortc_case_1_result.json",
    "Live Case 1 Pre-Discharge Case Notes": "eortc_case_1_pre_discharge_result.json",
}

TO_SHOW_CASES = [
    "Live Case 1 Admission Case Notes", 
    "Live Case 1 Pre-Discharge Case Notes", 
]

## Streamlit UI


if st.session_state.get("input_data") is None:
    st.session_state.input_data = {}
    for key, value in st.session_state.input_mapping_dict.items():
        if key not in TO_SHOW_CASES:
            continue
        st.session_state.input_data[key] = get_text_from_docx(f"{folder_stem}eortc/{value}")
input_mapping_dict = st.session_state.input_mapping_dict

output_mapping_dict = st.session_state.output_mapping_dict

if st.session_state.get("output_data") is None:
    st.session_state.output_data = {}
    for key, value in st.session_state.output_mapping_dict.items():
        if key not in TO_SHOW_CASES:
            continue
        if not os.path.exists(f"{folder_stem}eortc/{value}"):
            result = extract_eortc_from_docx(f"{folder_stem}eortc/{st.session_state.input_mapping_dict[key]}")
            with open(f"{folder_stem}eortc/{value}", 'w') as file:
                result = extract_eval_json(result)
                json.dump(result, file, indent=4)
        with open(f"{folder_stem}eortc/{value}", 'r') as file:
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
            form_submit_button = st.form_submit_button("Extract EORTC", type="primary", use_container_width=True)
    
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
            display_output = extract_eortc_from_text(case_notes_input)
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
            # df.index = ["Mobility", "Self Care", "Usual Activities", "Pain / Discomfort", "Anxiety / Depression"]

            # Select and rename the columns
            df = df[["final_score", "supporting_statements"]]
            df.columns = ["Final Score", "Supporting Statements From Case Notes"]
            st.dataframe(df)
        else:
            st.write("No data to extracted.")
        
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
        
        categorymap = {
            "q1_trouble_doing_strenuous_activities": "Do you have any trouble doing strenuous activities, like carrying a heavy shopping bag or a suitcase?",
            "q2_trouble_taking_long_walk": "Do you have any trouble taking a long walk?",
            "q3_trouble_taking_short_walk": "Do you have any trouble taking a short walk outside of the house?",
            "q4_need_to_stay_in_bed_or_chair": "Do you need to stay in bed or a chair during the day?",
            "q5_need_help_with_eating_dressing_washing_toilet": "Do you need help with eating, dressing, washing yourself, or using the toilet?",
            "q6_limited_in_work_or_daily_activities": "Were you limited in doing either your work or other daily activities?",
            "q7_limited_in_hobbies_or_leisure_activities": "Were you limited in pursuing your hobbies or other leisure time activities?",
            "q8_difficulty_concentrating": "Have you had difficulty in concentrating on things, like reading a newspaper or watching television?",
            "q9_feel_tense": "Did you feel tense?",
            "q10_worry": "Did you worry?",
            "q11_feel_irritable": "Did you feel irritable?",
            "q12_feel_depressed": "Did you feel depressed?",
            "q13_difficulty_remembering": "Have you had difficulty remembering things?",
            "q14_interference_with_family_life": "Has your physical condition or medical treatment interfered with your family life?",
            "q15_interference_with_social_activities": "Has your physical condition or medical treatment interfered with your social activities?",
            "q16_overall_health_rating": "How would you rate your overall health during the past week?",
            "q17_overall_quality_of_life_rating": "How would you rate your overall quality of life during the past week?"
        }
        # Define the colormap with 17 distinct light colors
        def generate_light_colors(n):
            colors = []
            for i in range(n):
                
                a = random.randint(0, 100)
                b = random.randint(0, 100 - a)
                c = 100 - a - b
                a+=10
                b+=10
                c+=10
                r,g,b = random.choice([(a,b,c), (a,c,b), (b,a,c), (b,c,a), (c,a,b), (c,b,a)])
                color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                # color = "#{:02x}{:02x}{:02x}".format(random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
                colors.append(color)
            return colors
        colors = generate_light_colors(17)
        question_list = list(categorymap.keys())
        colormap = {f"{question_list[i]}": colors[i] for i in range(17)}
        taggingmap = {f"{question_list[i]}": f"Q{i+1}" for i in range(17)}
        # # Define the colormap
        # colormap = {
        #     "mobility": "#f08080",
        #     "self_care": "#e0a050",
        #     "usual_activities": "#f0f090",
        #     "pain_discomfort": "#80f080",
        #     "anxiety_depression": "#a0a0f0",
        # }
        # # Define the tagging map
        # taggingmap = {
        #     "mobility": "MOB",
        #     "self_care": "S.C",
        #     "usual_activities": "U.A",
        #     "pain_discomfort": "P/D",
        #     "anxiety_depression": "A/D",
        # }
        # categorymap = {
        #     "mobility": "Mobility",
        #     "self_care": "Self Care",
        #     "usual_activities": "Usual Activities",
        #     "pain_discomfort": "Pain / Discomfort",
        #     "anxiety_depression": "Anxiety / Depression",
        # }

        # Function to wrap the sentence with HTML span and color
        def wrap_sentence_with_color(sentence, category, score):
            total_score = 7 if category.startswith("q16") or category.startswith("q17") else 4
            color = colormap[category]
            tagging = taggingmap[category]
            return f'<span style="background-color: #c0c0c0; border-radius: 0.5rem; padding:0.2rem 0.5rem 0.1rem;color:black;" title="{categorymap[category]}">{sentence} <span style="background-color:{color};color:white;border-radius:0.5rem; padding: 0.1rem 0.5rem; margin:0.1rem 0; font-size:0.8rem;"><strong>{tagging}</strong>: {score}/{total_score}</span></span>'

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
        with st.expander("Legend (click to show/hide). Hover above highlight to see full question.", expanded=False):
            st.markdown(
                """
                <div style='background-color: #0e1117; border-radius: 0.5rem; padding: 0.2rem 0.5rem; color: white; margin: 0.5rem 0; display: flex; flex-grow: 1; width: 100%; flex-direction: column; flex-wrap: wrap; align-items: start;gap: 0.2rem;'>
                """
                +
                # <span style='background-color: #f08080; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>MOB</strong>: Mobility</span>
                # <span style='background-color: #e0a050; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>S.C</strong>: Self Care</span>
                # <span style='background-color: #f0f090; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>U.A</strong>: Usual Activities</span>
                # <span style='background-color: #80f080; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>P/D</strong>: Pain / Discomfort</span>
                # <span style='background-color: #a0a0f0; border-radius: 0.5rem; padding: 0.1rem 0.5rem; margin: 0.1rem;'><strong>A/D</strong>: Anxiety / Depression</span>
                "\n".join([f'<span style="background-color:{color};display:inline-block;width:100%;color:white;margin:1rem;border-radius:0.5rem; padding: 0.1rem 0.5rem; margin:0.1rem 0;"><strong>{taggingmap[category]}</strong>: {categorymap[category]}</span>' for category, color in colormap.items()])
                +
                """
                </div>
                """,
                unsafe_allow_html=True
            )
        with st.container(height=500, border=True):
            st.markdown(annotations_input, unsafe_allow_html=True)

