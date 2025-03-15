## Standalone streamlit app for loading anottations
# input: result string as dict
import streamlit as st
# from faiss_generator import getIndex, compareQuery
from functions.idea_1_annotate import *

def runAnnotate(question):
    
    # TODO
    ans = getAnswer(question)    # <--------------- ans should give json output from the model
    # example format
    """{
    "answers": [
        {
        "cited_sentence": "Currently, they are unable to walk due to pain.",
        "category": "mobility",
        "score": "5"
        },
        {
        "cited_sentence": "Patient states they were previously independent / required some assistance with dressing and hygiene but now need full assistance.",
        "category": "self-care",
        "score": "5"
        },
        {
        "cited_sentence": "Reports significant difficulty performing household chores and leisure activities due to pain and immobility.",
        "category": "usual activities",
        "score": "4"
        },
        {
        "cited_sentence": "Rates pain as [X/10] at rest and [X/10] with movement.",
        "category": "pain/discomfort",
        "score": "4"
        },
        {
        "cited_sentence": "Reports feeling [slightly/moderately/severely] anxious about mobility and future recovery.",
        "category": "anxiety/depression",
        "score": "3"
        }
    ]
    }"""

    output = annotateQuery(ans, question)
    return output

st.title("Chat Interface")

user_input = st.text_area("Enter your message:", height = 300)
if user_input:
    output = runAnnotate(user_input)
    # Create side-by-side columns
    col1, col2 = st.columns(2)
    print(output)
    dark_mode_css = """
    <style>
        body, .st-emotion-cache-uf99v8 {
            background-color: black !important;
            color: white !important;
        }
        .entities {
            line-height: 2;
        }
        .entities span {
            padding: 0.25em 0.35em;
            border-radius: 0.25em;
            margin: 0 0.25em;
            font-weight: bold;
        }
        .entities .mobility { background: #FFDD44; color: black; }
        .entities .self-care { background: #FF88AA; color: black; }
        .entities .usual { background: #77DD77; color: black; }
        .entities .pain { background: #FF4444; color: white; }
        .entities .depression { background: #8888FF; color: white; }
    </style>
    """
    with col1:
        st.subheader("User Input")
        lorem = (
            f"""<div class="entities" style="line-height: 2.5; direction: ltr">{user_input}</div>"""
        )
        st.markdown(dark_mode_css+lorem, unsafe_allow_html=True)

        # st.components.v1.html(dark_mode_css + lorem, height=500, scrolling=True)
        # st.write(user_input)

    with col2:
        st.subheader("Annotated Text")
        # Custom CSS for tooltip        
        st.markdown(dark_mode_css+output, unsafe_allow_html=True)

        # st.components.v1.html(dark_mode_css + output, height=500, scrolling=True)
        # st.html("""
        #     <style>
        #     .tooltip {
        #         background-color: yellow;
        #         font-weight: bold;
        #         cursor: pointer;
        #         padding: 2px;
        #         border-radius: 3px;
        #     }
        #     .tooltip:hover::after {
        #         content: attr(title);
        #         position: absolute;
        #         background: black;
        #         color: white;
        #         padding: 5px;
        #         border-radius: 5px;
        #         font-size: 12px;
        #         white-space: nowrap;
        #     }
        #     </style>
        #     <div>
        #         """ + output + """
        #     </div>
        # """)

    spacyhtml = """
       <div class="entities" style="line-height: 2.5; direction: ltr">
<mark class="entity" style="background: #f08080; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
     Currently, they are unable to walk due to pain.
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">mobility</span>
</mark>
<br>Self-Care: 
<mark class="entity" style="background: #e02020; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    Patient states they were previously independent / required some assistance with dressing and hygiene but now need full assistance.
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">self-care</span>
</mark>

<mark class="entity" style="background: #9bddff; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    Reports significant difficulty performing household chores and leisure activities due to pain and immobility
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">usual-activities</span>
</mark>
<br>Usual Activities: Reports significant difficulty performing household chores and leisure activities due to pain and immobility.<br>Pain Assessment:<br>Describes the pain as [sharp/dull/aching], localized to the [hip/thigh/groin], with radiation to [if applicable].
<mark class="entity" style="background: #0bd0ff; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    
Rates pain as [X/10] at rest and [X/10] with movement.
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">pain-discomfort</span>
</mark>
<br>Pain worsens with attempted movement and is relieved sli
<mark class="entity" style="background: #008080; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    gh
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">anxiety-depression</span>
</mark>
tly with rest.<br>Psychosocial &amp; Emotional Well-being:<br>Appears [calm/anxious/distressed] about the injury and hospitalization.<br>Reports feeling [slightly/moderately/severely] anxious about mobility and future recovery.<br>No signs of overt depression but expresses concerns about burdening family.<br><br></div>
<div class="entities" style="line-height: 2.5; direction: ltr">SOAP Note – Subjective (S):<br>Chief Complaint:<br>Patient presents with left/right hip pain after a fall at home. Unable to bear weight.<br>History of Present Illness:<br>[Patient's Name] is a [age]-year-old [gender] with a background history of [relevant past medical history, e.g., hypertension, diabetes, osteoporosis], who was admitted for a hip fracture following a fall from standing height. The patient reports severe pain in the [left/right] hip, worsening with movement. No preceding dizziness, loss of consciousness, or other neurological symptoms. No head trauma or loss of bowel/bladder control.<br>Functional Status Prior to Admission:<br>Walking Ability: Patient reports that before the fall, they were [ambulant without aid / using a walking stick / using a frame / wheelchair-bound].
<mark class="entity" style="background: #f08080; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
     Currently, they are unable to walk due to pain.
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">mobility</span>
</mark>
<br>Self-Care: Patient states they were previously independent / required some assistance with dressin
<mark class="entity" style="background: #e02020; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    g 
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">self-care</span>
</mark>
and hy
<mark class="entity" style="background: #9bddff; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    gi
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">usual-activities</span>
</mark>
ene but now need full assistance.<br>Usual Activities: Reports significant difficulty performing household chores and leisure activities due to pain and immobility.<br>Pain Assessment:<br>Describes the pain as [sharp/dull/aching], localized to the [hip/thigh/groin], with radiation to [if applicable].
<mark class="entity" style="background: #0bd0ff; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    
Rates pain as [X/10] at rest and [X/10] with movement.
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">pain-discomfort</span>
</mark>
<br>Pain worsens with attempted movement and is relieved slightly with rest.<br>Psychosocial &amp; Emotional Well-being:<br>Appears [calm/anxious/distressed] about the injury and hospitalization.<br>
<mark class="entity" style="background: #008080; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    Reports feeling [slightly/moderately/severely] anxious about mobility and future recovery.
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">anxiety-depression</span>
</mark>
<br>No signs of overt depression but expresses concerns about burdening family.<br><br></div>
    """
    # st.components.v1.html(dark_mode_css+spacyhtml, height=500, scrolling=True)
    st.markdown(dark_mode_css+spacyhtml, unsafe_allow_html=True)
