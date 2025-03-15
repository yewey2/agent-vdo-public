# imports
import os
import glob

try:
    import iris
    iris_present = True
except:
    from functions.faiss_generator import *
    iris_present = False

import time
import os
import json
import ast
import re

import pandas as pd
import streamlit as st
from google import genai

from sentence_transformers import SentenceTransformer, util

from functions.idea_1 import *

## Streamlit Configs and default headers
logo_path = None
if os.path.exists("./images/logo.png"):
    logo_path = "./images/logo.png"
    folder_stem = ""
elif os.path.exists("/agent_vdo_mini/images/logo.png"):
    logo_path = "/agent_vdo_mini/images/logo.png"
    folder_stem = "/agent_vdo_mini/"
st.set_page_config(
    page_title="EQ-5D Insights",
    page_icon=logo_path,
    # layout="centered",
    # layout="wide",
    layout="centered",
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

input_csv_path = f"{folder_stem}eq5d/eq5d_actual_scores_disc.csv"
# input_csv_path = f"{folder_stem}eq5d/eq5d_scores.csv"

# Load the CSV of output data
data = pd.read_csv(f'{input_csv_path}')

if iris_present:
    ## Load intersys database
    username = '_system'
    password = 'sys'
    hostname = os.getenv('IRIS_HOSTNAME', 'localhost')
    port = '1972' 
    namespace = 'USER'
    CONNECTION_STRING = f"{hostname}:{port}/{namespace}"

    # Note: Ideally conn and cursor should be used with context manager or with try-execpt-finally 
    conn = iris.connect(CONNECTION_STRING, username, password)
    cursor = conn.cursor()

    tableName = "SchemaName.TableName"

    tableDefinition = "(case_number VARCHAR(255), entity VARCHAR(4096), first_header VARCHAR(4096), entity_vector VECTOR(DOUBLE, 384))"

    try:
        cursor.execute(f"CREATE TABLE {tableName} {tableDefinition}")
        intersys_loaded = True
    except:
        try:
            cursor.execute(f"DROP TABLE {tableName}")  
            cursor.execute(f"CREATE TABLE {tableName} {tableDefinition}")
            intersys_loaded = True        
        except Exception as e:
            intersys_loaded = False
            print("Intersys not working!")
            print(e)
else:
    intersys_loaded = False

## New functions
def extract_entities(text):
    if len(text) == 0:
        return {"error": "No Discharge Summary found."}
    # if "Issues and progress".lower() in text.lower():
    #     print("stripped issues and progress")
    #     text = text[text.lower().index("Issues and progress".lower()):]
    print(text)
    try:
        # header_pattern=r"^\s*[\dA-Za-z#*-]+\s*[\.\)\-]*\s+"  # Matches headers like "1. ", "1) ", "1- ", "1.1 "
        # header_pattern = r"^\d+\."
        lines = text.split("\n")
        paragraphs = []
        current_paragraph = []
        firstheader = ""
        startchecking = False

        for line in lines:
            if "issue" and "progress" in line.lower():
                startchecking=True
                continue
            if startchecking:
                line = line.strip()
                # if re.match(header_pattern, line):  # Detects headers dynamically
                if '1.' in line:
                    if firstheader == "":
                        firstheader = line[2:].strip()
                    if current_paragraph:
                        paragraphs.append(current_paragraph)
                    current_paragraph = [line[2:].strip(),]
                elif current_paragraph:  # Append body text to the last detected header
                    current_paragraph.append(line[2:].strip())

        if current_paragraph:
            paragraphs.append(current_paragraph)

        return {firstheader: ["/n".join(x) for x in paragraphs]}
    except:
        from dotenv import load_dotenv
        load_dotenv(f"{folder_stem}/.env") ## load from intersys directory
        load_dotenv("./.env") ## load from current directory
        load_dotenv("../.env") ## load from parent directory

        ## Currently using gemini, replace as needed.
        API_KEY = os.environ.get("gemini_key")
        client = genai.Client(api_key=API_KEY)
        model_name = "gemini-2.0-flash-lite"
        # """Retrieve annotations from Gemini API and return structured JSON."""
            
        # Define the prompt
        prompt = f"""
        Analyze the following doctor notes and extract word-for-word each individual issue as a separate entity:
        
        Return the result directly as a JSON with:
        - "entities": list of strings: each issue (header + newline + each points separated by newline) as a separate string

        Do not generate explanations, only return the valid JSON object as the response.

        Doctor Notes:
        {text}
        """

        # Generate response
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                # system_instruction='you are a story teller for kids under 5 years old',
                max_output_tokens= 1000,
                # top_k= 2,
                # top_p= 0.5,
                # temperature= 0.5,
                # response_mime_type= 'application/json',
                # stop_sequences= ['\n'],
                seed=42,
            ),
            )
        print(response.text)
        print("responsed ended")
        try:
            start_index = response.text.index('{')
            end_index = response.text.rindex('}')
            
            # Slice the string from the first '{' to the last '}'
            json_content = response.text[start_index:end_index+1]
            # Extract and parse JSON response
            extracted_data = json.loads(json_content)

            verified_sentences = []
            # check for source strings
            for x in extracted_data[list(extracted_data.keys())[0]]:
                if x in text:
                    verified_sentences.append(x)
            # extracted_data[list(extracted_data.keys())[0]] = verified_sentences
            return {verified_sentences[0].split("\n")[0] : verified_sentences} if verified_sentences else {"error": "No valid entities found by gemini"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse response as JSON"}

def save_to_database(casenumber, ent1, first, ent2):
    try:
        sql = f"""
            INSERT INTO {tableName}
            (case_number, entity, first_header, entity_vector) 
            VALUES (?, ?, ?, TO_VECTOR(?))
        """
        
        start_time = time.time()
        # Prepare the list of tuples (parameters for each row)
        data = [
            (
                casenumber, 
                entstr,
                first, 
                str(entscore) 
            )
            for entstr, entscore in zip(ent1, ent2)
        ]
        
        cursor.executemany(sql, data)
        end_time = time.time()
        print(f"time taken to add {len(ent1)} entries: {end_time-start_time} seconds")

        return True
    except:
        return False

def save_to_json(data, file_path):
    """
    Save the given data to a JSON file.

    :param file_path: str, the path where the JSON file should be saved.
    :param data: dict or list, the data to be saved in JSON format.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)  # Pretty print with indentation
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

## load model
with st.spinner("Processing..."):
    # Load the SentenceTransformer model
    if not st.session_state.get('model', None):
        model = SentenceTransformer('all-MiniLM-L6-v2')
        st.session_state['model'] = model
    else:
        model = st.session_state['model']
        
categorymap = {
    "mobility": "Mobility",
    "self_care": "Self Care",
    "usual_activities": "Usual Activities",
    "pain_discomfort": "Pain/Discomfort",
    "anxiety_depression": "Anxiety/Depression",
}
category_reversemap = {v: k for k, v in categorymap.items()}

category_select = st.selectbox('Select Category', categorymap.values())
category = category_reversemap[category_select]
categorydescription = {
  "mobility": "mobility issues: walking, walking about, problems in walking",
  "self_care": "self_care issues: washing, dressing, problems washing, problems dressing",
  "usual_activities": "usual_activities issues: work, study, housework, family, leisure activities, problems doing usual activities",
  "pain_discomfort": "pain_discomfort issues: pain, discomfort, slight pain, severe pain",
  "anxiety_depression": "anxiety_depression issues: anxious, depressed, slight anxiety, severe depression"
}


change_type = st.radio('Outcome of stay', ['Improve (score decreases)', 'Worsen (score increases)', "No Change"])
change_map = {
    "Improve (score decreases)": "improvement",
    "Worsen (score increases)": "worsening",
    "No Change": "no change"
}

# TODO create outcome column and process change_type to the outcome column
data['score_difference'] = data.apply(lambda row: row['final_score_1'] - row['final_score_2'] if row['captured_in_doc_1'] == True and row['captured_in_doc_2'] == True else float('nan'), axis=1)
data['change_type'] = data.apply(lambda row: "improvement" if row['score_difference'] > 0 else ("worsening" if row['score_difference'] < 0 else ("no change" if row['score_difference'] != float('nan') else "nan")), axis=1)
# data["supporting_statements_1"] = data["supporting_statements_1"].apply(lambda x: ast.literal_eval(x) if x not in ["", "notfound"] else [])
# data["supporting_statements_2"] = data["supporting_statements_2"].apply(lambda x: ast.literal_eval(x) if x not in ["", "notfound"] else [])
data["supporting_statements_1"] = data["supporting_statements_1"].apply(ast.literal_eval)
data["supporting_statements_2"] = data["supporting_statements_2"].apply(ast.literal_eval)

supported_case_numbers = ['case_1.json', '7', '8','9','10','11']

print(data[['case_number', 'dimension_1', 'change_type', 'captured_in_doc_1', 'captured_in_doc_2']])
## filter rows (currently filter only for case_1)
filtered_data = data[
                    (data['case_number'].isin(supported_case_numbers)) &          #TODO <------------------------NOTE: currently hardcoded
                    (data['dimension_1'] == category) & 
                    (data['change_type'] == change_map[change_type]) &
                    (data['captured_in_doc_1'] == True) &
                    (data['captured_in_doc_2'] == True)
                    #  & (data['date'] >= pd.to_datetime(start_date)) & 
                    #  (data['date'] <= pd.to_datetime(end_date))
                     ]

print("processing", category_select,change_type)
# Process each row
results = []
isdischarge = []
eq5dtodisplay = []
new_column_names = {
    "case_number": "Case ID",
    "dimension_1": "EQ5D_Category",
    "final_score_1": "Score_Adm",
    "supporting_statements_1": "cited_Adm",
    "final_score_2": "Score_Disc",
    "supporting_statements_2": "cited_Disc",
    "score_difference": "score_difference"
}

for _, row in filtered_data.iterrows():
    ## extract case number
    case_int = int("".join([char for char in row['case_number'] if char.isdigit()]))
    print(case_int)
    ## generate entities

    if intersys_loaded and iris_present:
        ## intersys: check for existing case_number
        sql = f"""
        SELECT case_number
        FROM {tableName}
        WHERE case_number = ?
        """
        cursor.execute(sql, [row['case_number'], ])
        # Fetch all results
        iscaseiniris = cursor.fetchall()
    else:
        iscaseiniris = []
    if len(iscaseiniris) == 0:
        entities = []
        
        ## check for existing entities json
        # Directory to search in
        directory_path = folder_stem + "eq5d/"
        
        # Use glob to find files that match the pattern
        json_files = glob.glob(os.path.join(directory_path, f'*{case_int}*entities*.json'))
        if len(json_files)>0:
            print("loading entities from json")
            try:
                with open(json_files[0], 'r', encoding='utf-8') as f:
                    entityjsondata = json.load(f)  # Load the JSON data from the file
                    print(entityjsondata)
                entities = list(entityjsondata.items())
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {f}")
            except Exception as e:
                print(e)
        else:
            print(f"No entities json found: {row['case_number']}")
            
            
        ## extract entitites
        if entities == []:
            #find source documents
            adm_files = glob.glob(os.path.join(directory_path, f'*{case_int}*synthetic*.docx'))
            print(adm_files)
            discharge = ""
            if len(adm_files) > 0:
                discindicator = [1 if "discharge" in f else 0 for f in adm_files]
                if 1 in discindicator:
                    try:
                        entitydocsdata = get_text_from_discharge(adm_files[discindicator.index(1)])  # Load the JSON data from the file
                        discharge = discharge + entitydocsdata
                        isdischarge.append(True)
                    except:
                        print(f"Error decoding discharge notes from file: {f}")
                else:
                    # for f in adm_files:
                    #     try:
                    #         entitydocsdata = get_text_from_docx(f)  # Load the JSON data from the file
                    #         discharge = discharge + entitydocsdata
                    #         isdischarge.append(True)
                    #     except:
                    print(f"No discharge files found for: {row['case_number']}")
                if len(isdischarge) == len(results):
                    isdischarge.append(False)
            else:
                print(f"No case files found for: {row['case_number']}")

            print(len(discharge))
            entitystr_json = extract_entities(discharge)
            if "error" not in entitystr_json.keys():
                # save entities to json
                # TODO: async
                save_to_json(entitystr_json, os.path.join(directory_path, f"case_{case_int}_entities.json"))
                entitystr_list = list(entitystr_json.items())
            else:
                print(f"entity extraction failed and no entities found. {row['case_number']}_{case_int}")
        else:
            entitystr_list = entities.copy()
            
        ## encode entitites
        entity_embedding = model.encode(entitystr_list[0][1], convert_to_tensor=True).tolist() #list of vectors

        ## save to intersys
        if intersys_loaded and iris_present:
            # TODO async
            save_to_database(row['case_number'], entitystr_list[0][1], entitystr_list[0][0], entity_embedding)
            # Calculate similarity score between entities and category
            category_embedding = model.encode(categorydescription[category], convert_to_tensor=True)
            entity_filtered = []
            for entitystr, entity in zip(entitystr_list[0][1], entity_embedding):
                similarity_score = util.pytorch_cos_sim(category_embedding, entity).item()
                if similarity_score > 0.25:  # Assuming a threshold of 0.5
                    entity_filtered.append(((entitystr.split("/n/n")[0]+ f" \n[Main Issue: {entitystr_list[0][0]}]").replace("*",""), similarity_score))
                else:
                    print((entitystr, similarity_score))
        else:
            faiss_index = getIndexFromText(entitystr_list[0][1], saveIndex = True, index_file = f"faiss_entities_{case_int}.bin", mdl_name = "all-MiniLM-L6-v2")
        
            # Calculate similarity score between entities and category
            dist, indices = compareQueryIssues(faiss_index, categorydescription[category], k=10)
            entity_filtered = []
            print(dist)
            for entitystr, entityscore in zip([entitystr_list[0][1][i] for i in indices], dist.flatten()):
                if entityscore > 0.25:  # Assuming a threshold of 0.5
                    entity_filtered.append(((entitystr.split("/n/n")[0]+ f" \n[Main Issue: {entitystr_list[0][0]}]").replace("*",""), entityscore))
                else:
                    print((entitystr, entityscore))
    elif iris_present and intersys_loaded:
        category_embedding = model.encode(category, convert_to_tensor=True).tolist()

        
        ## intersys: extract vectors and scores
        sql = f"""
            SELECT TOP ? case_number, entity, first_header, VECTOR_DOT_PRODUCT(TO_VECTOR(entity_vector), TO_VECTOR(?))
            FROM {tableName}
            WHERE case_number = ?        
            ORDER BY VECTOR_DOT_PRODUCT(TO_VECTOR(entity_vector), TO_VECTOR(?)) DESC
        """
        numberOfResults = 15
        # Execute the query with the number of results and search vector as parameters
        cursor.execute(sql, [numberOfResults, str(category_embedding), row['case_number'], str(category_embedding)])
    
        # Fetch all results
        entities_iris = cursor.fetchall()
        
        entity_filtered = []
        for case_id, entitystr, first, entityscore in entities_iris:
            if entityscore > 0.25:  # Assuming a threshold of 0.5
                entity_filtered.append(((entitystr.split("/n/n")[0]+ f" [Main Issue: {first}]").replace("*",""), entityscore))
        
    
    # Sort Entitities
    sorted_entities = sorted(entity_filtered, key=lambda x: x[1], reverse=True)
    results.append((case_int, sorted_entities))

    # Print row to eq5d
    eq5dtodisplay.append(pd.DataFrame(row[["case_number", "dimension_1", "final_score_1", "supporting_statements_1", "final_score_2", "supporting_statements_2", "score_difference"]])
                      .rename(columns=new_column_names))
# Aggregate top 5 causes of decrease/increase across cases(rerank from above)
# Flatten results and rerank to get top 5 causes
all_entities = [(case_no, x[0], x[1]) for case_no, sublist in results for x in sublist]
sorted_all_entities = sorted(all_entities, key=lambda x: x[2], reverse=True)

# Get top 5 entities
top_5_entities = sorted_all_entities[:5]
# Add custom CSS for row height
st.markdown("""
    <style>
        .streamlit-expanderHeader {
            line-height: 30px;  /* Adjust this value to change row height */
        }
        .stDataFrame tbody tr {
            height: 40px;  /* Adjust this value to change row height */
        }
    </style>
""", unsafe_allow_html=True)
if len(top_5_entities) == 0:
    # st.write(f"## Aggregated Top 5 issues related to {change_map[change_type]} of {category_select} across cases:")
    st.warning("No results found for selected category and change in outcome. Please try again with different filters.")
else:
    # Display top 5 entities (expand dropdown: title "aggregated")
    st.write(f"## Aggregated Top 5 issues related to {change_map[change_type]} of {category_select} across cases:")
    st.dataframe(pd.DataFrame(top_5_entities, columns=["Case ID", "Issues/Progress", "Similarity Score to category"]), hide_index=True)
    # for case_no, entity, score in top_5_entities:
    #     st.write(f"Entity: {entity}, Similarity Score: {score}, From Case ID: {case_no}")

    # Display Each case entities (expand dropdown: title f"{case_id}")
    for result, eq5d_df in zip(results, eq5dtodisplay):
        with st.expander(f"Case ID: {str(result[0])}"):
            # Display EQ5D table
            st.write(f"EQ5D table for {category_select} Scores:")  # <-------------------------------------TODO: Add EQ5D table here
            # eq5d_df.set_index("Case ID", inplace=True)
            st.table(eq5d_df.T)

            # Display entities from Discharge Summary
            st.write("Issues extracted from Discharge Summary")
            st.dataframe(pd.DataFrame(result[1], columns=["Issues/Progress", "Similarity Score to category"]), hide_index=True)
            # for entity, score in result[1]:
            #     st.write(f"Issue/Progress: {entity}, Similarity Score: {score}")
# if not results:
    # st.warning("No results found for selected category and change in outcome. Please try again with different filters.")




# data['category'] = data['dimension_1']  # Placeholder for category column
# data['change_type'] = data.apply(lambda row: "Improve" if row['final_score_2'] > row['final_score_1'] else ("Worsen" if row['final_score_2'] < row['final_score_1'] else "No Change"), axis=1)

# ## TODO: 
# data['discharge_summary'] = "This is a placeholder discharge summary."

# data['id'] = data['case_number']


# # Streamlit user input
# st.write("## Filter for cases based on category and changes in outcomes in EQ5D")
# categorymap = {
#     "mobility": "Mobility",
#     "self_care": "Self Care",
#     "usual_activities": "Usual Activities",
#     "pain_discomfort": "Pain/Discomfort",
#     "anxiety_depression": "Anxiety/Depression",
# }
# category_reversemap = {v: k for k, v in categorymap.items()}

# category = st.selectbox('Select Category', [categorymap[c] for c in data['category'].unique()])
# category = category_reversemap[category]

# change_type = st.radio('Outcome of stay', ['Improve', 'Worsen', "No Change"])
# # start_date = st.date_input('Start Date')
# # end_date = st.date_input('End Date')

# # Filter for rows based on user input
# filtered_data = data[(data['category'] == category) & 
#                      (data['change_type'] == change_type) 
#                     #  & (data['date'] >= pd.to_datetime(start_date)) & 
#                     #  (data['date'] <= pd.to_datetime(end_date))
#                      ]

# with st.spinner("Processing..."):
#     # Load the SentenceTransformer model
#     if not st.session_state.get('model', None):
#         model = SentenceTransformer('all-MiniLM-L6-v2')
#         st.session_state['model'] = model
#     else:
#         model = st.session_state['model']
    

# def extract_entities(text):
#     ## TODO
#     # Placeholder for entity extraction function
#     return ['entity1', 'entity2']


# # Process each row
# results = []
# for _, row in filtered_data.iterrows():
#     discharge_summary = row['discharge_summary']
#     # Extract entities from discharge summary (LLM) OR load from database if present
#     if 'entities' not in row or pd.isna(row['entities']):
#         # Assuming a function `extract_entities` that extracts entities from text
#         entities = extract_entities(row['discharge_summary'])
#         row['entities'] = ','.join(entities)
#     else:
#         entities = row['entities'].split(',')
#     # For simplicity, let's assume entities are already extracted and stored in the row
#     entities = row['entities'].split(',')
    
#     # Calculate similarity score between entities and category
#     category_embedding = model.encode(category, convert_to_tensor=True)
#     entity_scores = []
#     for entity in entities:
#         entity_embedding = model.encode(entity, convert_to_tensor=True)
#         similarity_score = util.pytorch_cos_sim(category_embedding, entity_embedding).item()
#         if similarity_score > 0.65:  # Assuming a threshold of 0.5
#             entity_scores.append((entity, similarity_score))
    
#     # Sort Entitities
#     sorted_entities = sorted(entity_scores, key=lambda x: x[1], reverse=True)
#     results.append((row['id'], sorted_entities))

# # Aggregate top 5 causes of decrease/increase across cases(rerank from above)
# # Flatten results and rerank to get top 5 causes
# all_entities = [x for sublist in [result[1] for result in results] for x in sublist]
# sorted_all_entities = sorted(all_entities, key=lambda x: x[1], reverse=True)

# # Get top 5 entities
# top_5_entities = sorted_all_entities[:5]

# # Display top 5 entities (expand dropdown: title "aggregated")
# st.write("## Aggregated Top 5 causes of decrease/increase across cases:")
# with st.expander("Aggregated"):
#     for entity, score in top_5_entities:
#         st.write(f"Entity: {entity}, Similarity Score: {score}")

# # Display Each case entities (expand dropdown: title f"{case_id}")
# for result in results:
#     with st.expander(f"Case ID: {result[0].split('.')[0]}"):
#         # Display EQ5D table
#         st.write("EQ5D Table Placeholder (Admission Notes, Last Notes before Discharge)")  # <-------------------------------------TODO: Add EQ5D table here

#         # Display entities from Discharge Summary
#         st.write("Issues extracted from Discharge Summary")
#         for entity, score in result[1]:
#             st.write(f"Entity: {entity}, Similarity Score: {score}")
# if not results:
#     st.warning("No results found for selected category and change in outcome. Please try again with different filters.")