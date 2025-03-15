import os
# from google import genai
import json
from rapidfuzz import process, fuzz
import spacy
from spacy import displacy
from spacy.tokens import Span
import numpy as np

# API_KEY = os.getenv("gemini_key")
# client = genai.Client(api_key=API_KEY)
# model_name = "gemini-2.0-flash-lite"

# def getAnswer(user_input):
# #    """HARDCODED ANSWER"""
# #     jsonstr =  """{
# #   "answers": [
# #     {
# #       "cited_sentence": "Currently, they are unable to walk due to pain.",
# #       "category": "mobility",
# #       "score": "5"
# #     },
# #     {
# #       "cited_sentence": "Patient states they were previously independent / required some assistance with dressing and hygiene but now need full assistance.",
# #       "category": "self-care",
# #       "score": "5"
# #     },
# #     {
# #       "cited_sentence": "Reports significant difficulty performing household chores and leisure activities due to pain and immobility.",
# #       "category": "usual activities",
# #       "score": "4"
# #     },
# #     {
# #       "cited_sentence": "Rates pain as [X/10] at rest and [X/10] with movement.",
# #       "category": "pain/discomfort",
# #       "score": "4"
# #     },
# #     {
# #       "cited_sentence": "Reports feeling [slightly/moderately/severely] anxious about mobility and future recovery.",
# #       "category": "anxiety/depression",
# #       "score": "3"
# #     }
# #   ]
# # }"""
#     # extracted_data = json.loads(jsonstr)
#     # return extracted_data
#     """Retrieve annotations from Gemini API and return structured JSON."""
        
#     # Define the prompt
#     prompt = f"""
#     Analyze the following doctor notes and extract medically relevant citations. 
#     For each cited sentence, categorize it under EQ5D (mobility, self-care, usual activities, pain/discomfort, anxiety/depression) 
#     and assign a score (1-5, where 1 = no issues, 5 = severe issues).
    
#     Return the result directly as a JSON with:
#     - "answers": list of 3 items:
#         - string "cited_sentence": Extracted medical text
#         - string "category": EQ5D category
#         - string "score": 1-5 scale

#     Do not generate explanations, only return the valid JSON object as the response.

#     Doctor Notes:
#     {user_input}
#     """

#     # Generate response
#     response = client.models.generate_content(
#         model=model_name, 
#         contents=prompt,
#         config=genai.types.GenerateContentConfig(
#             # system_instruction='you are a story teller for kids under 5 years old',
#             max_output_tokens= 400,
#             # top_k= 2,
#             # top_p= 0.5,
#             # temperature= 0.5,
#             # response_mime_type= 'application/json',
#             # stop_sequences= ['\n'],
#             seed=42,
#         ),
#            )
#     print(response.text)
#     print("responsed ended")
#     try:
#         start_index = response.text.index('{')
#         end_index = response.text.rindex('}')
        
#         # Slice the string from the first '{' to the last '}'
#         json_content = response.text[start_index:end_index+1]
#         # Extract and parse JSON response
#         extracted_data = json.loads(json_content)
#         return extracted_data
#     except json.JSONDecodeError:
#         return {"error": "Failed to parse response as JSON"}

def annotateQuery(answer, user_input, threshold=80):
    """Annotate the user input with the extracted citations."""
    if "error" in answer.keys():
        return "An error occurred while processing the request"
    label_list = ['O', 'mobility', 'self-care', 'usual-activities', 'pain-discomfort', 'anxiety-depression']
    label_key = ['placeholdernotpresentinsample', 'mobility', 'self-care', 'usual activities', 'pain/discomfort', 'anxiety/depression']
    label_entity_list = {label_key[i]: f'LABEL_{i}' for i in range(len(label_list))} 

    # Extract the cited sentences
    cited_sentences = answer["answers"]
    note_sentences = user_input.split(".")  # Ensure proper sentence splitting
    tokens = []
    label_list_after =[]
    token_start = 0  # Number of tokens before start
    # token_end = len(user_input)  # Number of tokens before end    
    for entry in cited_sentences:
        sentence = entry["cited_sentence"].strip(".")  # Remove trailing period
        category = entry["category"]
        score = entry["score"]
        print(sentence)
        # Exact match check
        if sentence in note_sentences:
            # start = doc.text.find(sentence)  # Find character index
            start = user_input[token_start:].find(sentence)
            start += token_start
            print(start)        
            if start == -1:
                continue  # Skip if not found

            end = start + len(sentence)+1 if sentence[-1]!="." else  start + len(sentence) # Compute end index

        else:
            # Fuzzy match closest sentence
            match, match_score, _ = process.extractOne(sentence, note_sentences, scorer=fuzz.partial_ratio)

            if match_score >= threshold:
                # start = doc.text.find(match)  # Find start index
                sentence = match
                start = user_input[token_start:].find(sentence)
                start += token_start
                if start == -1:
                    continue  # Skip if not found
                
                end = start + len(sentence)+1 if sentence[-1]!="." else  start + len(sentence) # Compute end index
            else:
                continue  # Skip low-confidence matches
        
        # Move left pointer
        token_start = end  # Number of tokens before start

        if category in label_entity_list.keys():
            entity_str = label_entity_list[category]
        else:
            entity_str = "LABEL_0"
        #save
        print("appended", {'entity': entity_str, 'score': np.float32(0.314159), 'index': len(tokens)+1, 'word': sentence, \
                       'start': start, 'end': end, "label": label_list[int(entity_str[-1])]+f" :{score}/5"})
        tokens.append({'entity': entity_str, 'score': np.float32(0.314159), 'index': len(tokens)+1, 'word': sentence, \
                       'start': start, 'end': end, "label": label_list[int(entity_str[-1])]+f" :{score}/5"})
        label_list_after.append(label_list[int(entity_str[-1])]+f" :{score}/5")
    params = [{"text": user_input,
               "ents": tokens,
               "title": None}]
    print(params)
    colormap = {
       "mobility": "#f08080",
       "self-care": "#e02020",
       "usual-activities": "#9bddff",
       "pain-discomfort": "#0bd0ff",
       "anxiety-depression": "#008080",
    }
    colorsdict = {}
    for x in label_list_after:
        for y in colormap.keys():
            if y in x and x not in colorsdict.keys():
               colorsdict[x] = colormap[y]
    html = displacy.render(params, style="ent", manual=True, options={
        "colors": colorsdict,
                # {
                   # "mobility": "#f08080",
                   # "self-care": "#e02020",
                   # "usual-activities": "#9bddff",
                   # "pain-discomfort": "#0bd0ff",
                   #  "anxiety-depression": "#008080",
               # },
    })
    print("displacy output")
    print(html)
    return html

    ents = []  # List to store entity spans

    used_char_ranges = []  # Track used character ranges to prevent overlap

    for entry in cited_sentences:
        sentence = entry["cited_sentence"].strip(".")  # Remove trailing period
        category = entry["category"]
        score = entry["score"]

        # Exact match check
        if sentence in note_sentences:
            start = doc.text.find(sentence)  # Find character index
            if start == -1:
                continue  # Skip if not found

            end = start + len(sentence)  # Compute end index

        else:
            # Fuzzy match closest sentence
            match, match_score, _ = process.extractOne(sentence, note_sentences, scorer=fuzz.partial_ratio)

            if match_score >= threshold:
                start = doc.text.find(match)  # Find start index
                if start == -1:
                    continue  # Skip if not found
                
                end = start + len(match)  # Compute end index
            else:
                continue  # Skip low-confidence matches

        # Check for overlap before adding a new entity
        if any(s <= start < e or s < end <= e for s, e in used_char_ranges):
            continue  # Skip overlapping spans

        # Convert character offsets to token indices
        token_start = len(doc[:start])  # Number of tokens before start
        token_end = len(doc[:end])  # Number of tokens before end

        # Create a spaCy Span and add to entity list
        span = Span(doc, token_start, token_end, label=f"{category} ({score}/5.0)")
        ents.append(span)

        # Store used range to avoid overlap
        used_char_ranges.append((start, end))

    # Assign non-overlapping entities correctly
    doc.set_ents(ents)

    # Render using displaCy
    html = displacy.render(doc, style="ent", jupyter=False)

    return html