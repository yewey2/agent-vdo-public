---
title: Agent VDO Public Demo
emoji: 🦉
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.42.2
app_file: app.py
pinned: false
short_description: This is a repository for Agent VDO, for HealthHack 2025
header: mini
---

# Agent VDO

This is a repository for Agent VDO, a submission to HealthHack 2025.

## Brief Summary

This solution targets the pain point of extracting Patient Reported Outcome Metrics (PROMs), a common metric used for value-driven outcomes.


# Disclaimer
**All patient case notes are simulated for demonstration purposes and are not real.**
Synthesized data is available on request to the authors.

# Running Intersystems (Instructions adapted from [here]([https://github.com/intersystems-community/hackathon-2024/tree/main](https://github.com/intersystems-community/hackathon-2024/blob/main/README.md)))

0. download github repository and create `.env` file
```Shell
git clone https://github.com/yewey2/agent-vdo-public.git
cd agent-vdo-public
```
In your `.env`  file you need the following:
```
OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"
OPENAI_API_KEY="INSERT_YOUR_OPENAI_API_KEY_HERE"
OPENAI_API_BASE='https://api.openai.com/v1/chat/completions'
gemini_key = 'INSERT_YOUR_GEMINI_API_KEY_HERE'
```
1. Install IRIS Community Edtion in a container. This will be your SQL database server.
```Shell
docker run -d --name iris-comm -p 1972:1972 -p 52773:52773 -p 8501:8501 -e IRIS_PASSWORD=demo -e IRIS_USERNAME=demo intersystemsdc/iris-community:latest
```
    
2.  After running the above command, you can access the System Management Portal via http://localhost:52773/csp/sys/UtilHome.csp with the login details `old` below:
|     | old | new |
| -------- | ------- | ------- |
| Username  |_system|_system|
| Password |SYS|sys|
3.  In the System Management Portal, when prompted to update your password, change your password to the `new` password.
4. Download the correct wheel for your operating system from [here](https://github.com/intersystems-community/hackathon-2024/tree/main/install). As an illustration we use `intersystems_irispython-5.0.1-8026-cp38.cp39.cp310.cp311.cp312-cp38.cp39.cp310.cp311.cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`.
Place it in your `agent-vdo-public` folder.
5. Start a virtual environment to install packages in. We chose to install directly in the IRIS docker container.
If using docker (optional): `docker exec -it iris-comm bash` or `docker exec -it --user root iris-comm bash` (if permission for venv and pip is denied)
make a virtual environment: ```python3 -m venv iris-env
source iris-env/bin/activate```
Ensure your python version is between 3.8 to 3.12: `python -V`

copy your files into docker (if using docker): `docker cp /mnt/c/Users/USERNAME/Documents/agent-vdo-public iris-comm:agent-vdo-public`

5. Install the iris python package with
`pip install agent-vdo-public/intersystems_irispython-5.0.1-8026-cp38.cp39.cp310.cp311.cp312-cp38.cp39.cp310.cp311.cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`
6. Install the rest of the requirements with
`pip install -r agent-vdo-public/requirements.txt`
7. Start the streamlit app with
`streamlit run agent-vdo-public/app.py`
8. Go to localhost:8501 to access your app.




