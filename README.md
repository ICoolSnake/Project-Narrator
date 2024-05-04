# Project-Narrator

__Project Narrator__ is a dynamic web application that employs state-of-the-art AI technology to humorously narrate the actions of individuals captured through a webcam. This system combines real-time video analysis with dynamic voice synthesis technology, creating a unique and engaging user experience. Users can choose from various narrator voices, each adding a distinct flavor to the narration.

## Features

- **Real-Time Video Analysis:** Utilizes the GPT-4-Vision API to interpret and narrate actions seen through a webcam.
- **Dynamic Voice Synthesis:** Incorporates the Eleven Labs API to generate voice narration in real-time, with multiple voice options.
- **User-Friendly Interface:** Developed using Flask, providing a simple and interactive web interface for users.

## Getting Started

To run Project Narrator on your local machine, follow these steps:

**Prerequisites:**
- Python 3.8+
- Flask
- ElevenLabs API subscription

## Setup

**Configure Voice IDs:** You need to enter your ElevenLabs voice IDs in the following files:
- index.html: Lines 64 to 96
- app.py: Line 66 and lines 101 to 149
- Enter your keys inside the .env file

## Usage

- **Changing Voices:** Select your desired narrator voice from the dropdown menu in the web interface.
- **Changing Language:** Select the language you desire from the circle-flag button in the web interface.
- **Starting the Narration:** Click on the "Start" button to activate the webcam and begin the narration.
