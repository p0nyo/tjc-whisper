# Description

A realtime speech-to-text program that can read audio input and output it onto a google doc.


Backend created using openai's whisper api and the google docs api.


Frontend gui created using the eel python library.

# Instructions

These instructions are for macos users.

### Google Docs API setup

1. create a google account
2. navigate to the google cloud console
3. navigate to the dashboard and create a new project

### Python environment setup

1. clone this repository.
```
git clone <repository link>
```
2.  navigate to the tjc-whisper directory
```
cd <link to>/tjc-whisper
```
3. create and enter a virtual environment
```
python -m venv venv
source venv/bin/activate
```
4. download required libraries
```
pip install -r requirements.txt
```
5. run the speech-to-text package
```
python -m speech-to-text
```
