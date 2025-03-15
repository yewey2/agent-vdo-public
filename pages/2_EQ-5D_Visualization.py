import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns

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
    page_title="EQ-5D Insights",
    page_icon=logo_path,
    # layout="centered",
    layout="wide",
    initial_sidebar_state="expanded",
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

# Load Data
@st.cache_data
def load_data():
    file_path = f"{folder_stem}eq5d/eq5d_actual_scores.csv"  # Adjust the path
    # file_path = f"{folder_stem}eq5d/eq5d_scores.csv"  # Adjust the path
    df = pd.read_csv(file_path)
    return df

df = load_data()

# Convert final_score columns to numeric (handling missing values)
df["final_score_1"] = pd.to_numeric(df["final_score_1"], errors="coerce")
df["final_score_2"] = pd.to_numeric(df["final_score_2"], errors="coerce")

# Compute New Metrics
df["score_difference"] = df["final_score_2"] - df["final_score_1"]
average_score_diff = df["score_difference"].mean()

# Count NULL values (missing scores)
null_score_1_count = df["final_score_1"].isna().sum()
null_score_2_count = df["final_score_2"].isna().sum()

# Compute total possible scores (same before and after)
total_possible_scores = df.shape[0]/5  


# Title
st.title("🏥 Overall Hospital EQ5D Status")

# Filters
departments = st.sidebar.multiselect("Select Department(s)", df['dept'].unique())
doctors = st.sidebar.multiselect("Select Doctor(s)", df['dr_name'].unique())

# Filter Data
filtered_df = df.copy()

if departments:
    filtered_df = filtered_df[filtered_df['dept'].isin(departments)]
if doctors:
    filtered_df = filtered_df[filtered_df['dr_name'].isin(doctors)]

#====================Key Metrics====================
st.subheader("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Cases", filtered_df["case_number"].nunique())
col2.metric("Avg EQ5D Score (Before)", round(filtered_df["final_score_1"].mean(), 2))
col3.metric("Avg EQ5D Score (After)", round(filtered_df["final_score_2"].mean(), 2))
col4.metric("Avg Score Change", round(average_score_diff, 2))

#====================Data Quality Indicators====================

# Recalculate missing counts dynamically using filtered_df
null_counts_dim1 = filtered_df[filtered_df["final_score_1"].isna()].groupby("dimension_1").size().reset_index(name="Missing Before")
null_counts_dim2 = filtered_df[filtered_df["final_score_2"].isna()].groupby("dimension_2").size().reset_index(name="Missing After")

# Merge missing counts into one dataframe
null_counts = pd.merge(null_counts_dim1, null_counts_dim2, left_on="dimension_1", right_on="dimension_2", how="outer").fillna(0)
null_counts = null_counts[["dimension_1", "Missing Before", "Missing After"]]
null_counts.set_index("dimension_1", inplace=True)

# Compute total possible scores based on the filtered dataset
filtered_total_possible_scores = filtered_df.shape[0] 

# Compute missing counts and percentages
missing_before = filtered_df["final_score_1"].isna().sum()
missing_after = filtered_df["final_score_2"].isna().sum()

missing_before_pct = (missing_before / filtered_total_possible_scores) * 100
missing_after_pct = (missing_after / filtered_total_possible_scores) * 100

st.subheader("⚠️ Data Quality Indicators")

col5, col6 = st.columns(2)
with col5:
    st.metric("Missing Initial Score (Before)", f"{missing_before} / {int(filtered_total_possible_scores)}")
    #st.write(f"**{missing_before_pct:.2f}%** missing")

with col6:
    st.metric("Missing Follow-up Score (After)", f"{missing_after} / {int(filtered_total_possible_scores)}")
    #st.write(f"**{missing_after_pct:.2f}%** missing")

#====================Missing EQ5D Scores by Dimension====================

# Grouped Bar Chart with Threshold Line
st.subheader("📊 Missing EQ5D Scores by Dimension")

fig, ax = plt.subplots(figsize=(10, 6))
null_counts.plot(kind="bar", ax=ax, width=0.75)

# Add a horizontal threshold line for total possible scores (from filtered data)
filtered_total_possible_scores = filtered_df.shape[0] / 5
ax.axhline(y=filtered_total_possible_scores, color='red', linestyle='--', linewidth=2, label="Total Possible Scores (Filtered)")

# Formatting
ax.set_ylabel("Number of Missing Scores")
ax.set_xlabel("EQ5D Dimension")
ax.set_title("Missing EQ5D Scores Before & After (Filtered)")
ax.legend(["Total Possible Scores", "Missing Before", "Missing After"])
ax.yaxis.set_major_locator(MaxNLocator(integer=True))

# Improve layout and readability
plt.xticks(rotation=45)
plt.grid(axis="y", linestyle="--", alpha=0.7)

st.pyplot(fig)

#====================Average Scores by Department====================

st.subheader("📌 Average EQ5D Scores by Department")

df_avg_scores = (
    filtered_df.groupby("dept")[["final_score_1", "final_score_2"]]
    .mean()
    .reset_index()
    .melt(id_vars="dept", var_name="Score Type", value_name="Average Score")
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x="dept", y="Average Score", hue="Score Type", data=df_avg_scores, ax=ax)
ax.set_ylabel("Average EQ5D Score")
ax.set_xlabel("Department")
ax.set_title("Department-wise EQ5D Score Averages")

# Manually Set Correct Legend Labels
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles, labels=["Average Score Before", "Average Score After"])  # Correctly renaming labels

# ax.legend(["Average Score Before", "Average Score After"])
st.pyplot(fig)

#====================Mean EQ5D Scores by Dimension (Before & After)====================


# Compute mean EQ5D scores for each dimension using filtered_df
mean_scores_dim1 = filtered_df.groupby("dimension_1")["final_score_1"].mean().reset_index()
mean_scores_dim2 = filtered_df.groupby("dimension_2")["final_score_2"].mean().reset_index()

# Merge both datasets to align dimensions for a dual-line plot
merged_scores = pd.merge(mean_scores_dim1, mean_scores_dim2, left_on="dimension_1", right_on="dimension_2", how="outer").fillna(0)
merged_scores = merged_scores[["dimension_1", "final_score_1", "final_score_2"]].set_index("dimension_1")

# Plot Line Chart for Before and After Scores
st.subheader("📊 Mean EQ5D Scores by Dimension (Before & After)")

# Melt Data for Correct Line Plot Formatting
merged_scores_reset = merged_scores.reset_index().melt(id_vars="dimension_1", var_name="Score Type", value_name="Mean Score")

# Plot with Explicit Hue Assignment
fig, ax = plt.subplots(figsize=(8, 5))
sns.lineplot(
    data=merged_scores_reset,
    x="dimension_1",
    y="Mean Score",
    hue="Score Type",
    markers=True,
    dashes=False,
    linewidth=2,
    ax=ax
)

# Formatting
ax.set_ylabel("Mean EQ5D Score")
ax.set_xlabel("EQ5D Dimension")
ax.set_title("Mean EQ5D Scores Across Dimensions (Before & After)")

# Manually Set Correct Legend Labels
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles, labels=["Before", "After"], title="Score Type")  # Correctly renaming labels

plt.xticks(rotation=45)
plt.grid(axis="y", linestyle="--", alpha=0.7)

st.pyplot(fig)


#====================Detailed Cases View====================


# Table - Raw Data Preview
st.subheader("📑 Detailed Cases View")
st.dataframe(filtered_df)

#====================Insights & Alerts - EQ5D Scores above threshold ====================

# # Insights Section
# st.subheader("📝 Insights & Alerts")

# # Filter high severity cases (score >= 4 in either before or after)
# high_severity_cases = filtered_df[(filtered_df["final_score_1"] >= 4) | (filtered_df["final_score_2"] >= 4)]

# # Count unique case numbers for high severity cases
# unique_high_severity_cases = high_severity_cases["case_number"].nunique()

# # Display alert and dataframe
# st.write(f"⚠️ **High Severity Cases Detected:** {unique_high_severity_cases} cases")
# st.dataframe(high_severity_cases)


# Insights Section
st.subheader("📝 Insights & Alerts")

# Define dynamic filtering criteria
criteria = []
if (filtered_df["final_score_1"] >= 4).any():
    criteria.append("Final Score Before (≥4)")
if (filtered_df["final_score_2"] >= 4).any():
    criteria.append("Final Score After (≥4)")

# Apply filtering logic
high_severity_cases = filtered_df[(filtered_df["final_score_1"] >= 4) | (filtered_df["final_score_2"] >= 4)]

# Count unique case numbers for high severity cases
unique_high_severity_cases = high_severity_cases["case_number"].nunique()

# Display results
st.write(f"⚠️ **High Severity Cases Detected:** {unique_high_severity_cases} cases")
st.write(f"📌 **Criteria Used:** {', '.join(criteria) if criteria else 'No cases matching severity threshold'}")

# Show filtered dataframe
st.dataframe(high_severity_cases)
