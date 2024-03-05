import base64
import numpy as np
import os
import pandas as pd
import pickle
import joblib
import requests
import streamlit as st
import time
from decouple import config
from sklearn.preprocessing import RobustScaler

# Spotify API functions
def get_access_token(client_id, client_secret):
    token_url = "https://accounts.spotify.com/api/token"
    client_credentials = f"{client_id}:{client_secret}"
    base64_credentials = base64.b64encode(client_credentials.encode("utf-8")).decode("utf-8")
    headers = {"Authorization": f"Basic {base64_credentials}"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        access_token = response.json().get("access_token", "")
        return access_token
    else:
        st.error(f"Error getting access token: {response.status_code} - {response.text}")
        return None

def search_track(query, access_token):
    url = "https://api.spotify.com/v1/search"
    params = {"q": query, "type": "track"}
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        tracks = response.json().get('tracks', {}).get('items', [])

        return tracks[:5]  # Limit to top 5 results
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching for track: {e}")
        return []

def get_track_info_and_features(track_id, access_token):
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        track_data = response.json()

        # Get audio features for the track
        audio_features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
        audio_features_response = requests.get(audio_features_url, headers=headers)
        audio_features_response.raise_for_status()
        audio_features = audio_features_response.json()

        return track_data, audio_features
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting track information and audio features for track ID {track_id}: {e}")
        return None, None

# Access environment variables
spotify_client_id = config("spotify_client_id")
spotify_client_secret = config("spotify_client_secret")

# Get the Spotify Access Token
spotify_access_token = get_access_token(spotify_client_id, spotify_client_secret)

# Streamlit App code
st.set_page_config(
    page_title="Spotify Talent Finder",
    page_icon="🎸",
    initial_sidebar_state="collapsed",  # Sidebar initially collapsed
)

# Remove whitespace from the top of the page and sidebar
st.markdown("""
        <style>
                div[data-baseweb="input"] input {
                    font-size: 1.3rem; /* Change font size as needed */
                }

               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 0rem;
                    padding-right: 0rem;
                }

                .st-emotion-cache-xujc5b p {
                    word-break: break-word;
                    margin-bottom: 0px;
                    font-size: 1.25rem; /* Change font size as needed */
                }

                p, ol, ul, dl {
                    margin: 0px 0px 1rem;
                    padding: 0px;
                    font-size: 1.25rem; /* Change font size as needed */
                    font-weight: 400;
                }
                .stRadio > div {
                    display: flex;
                    justify-content: center; /* Center alignment */
                }

                .stRadio label {
                    margin-left: 5px; /* Change margin as needed */
                    line-height: 1.5rem; /* Center height */
                }
        </style>
        """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: white;'>Spotify Talent Finder</h1>", unsafe_allow_html=True)

# Input field for the song name
query = st.text_input("Search for a song:")

# Variable to store the selected track ID
selected_track_id = None

ph = st.empty()

# Step 1: Select the song
if query:  # Only if a search query is present
    tracks = search_track(query, spotify_access_token)
    if tracks:
        with ph.container():
            st.write("Found tracks:")
            track_options = [f"{track['name']} by {', '.join([artist['name'] for artist in track['artists']])}" for track in tracks]
            selected_track = st.radio("Select a track:", track_options)

            # User clicked the button, store the selected track ID
            selected_track_id = [track['id'] for track in tracks if selected_track.startswith(track['name'])][0]

            # Display the prediction button
            predict_button = st.button("Predict the popularity")
            # Display the listen button
            listen_button = st.button("Listen to the song")
    else:
        pass  # Skip the warning

# Step 2: Display track information and audio features
if selected_track_id:
    # Play song preview
    if listen_button:
        ph.empty()
        track_data, audio_features = get_track_info_and_features(selected_track_id, spotify_access_token)
        preview_url = track_data.get('preview_url', None)
        if preview_url:
            st.subheader("Audio Preview:")

            # Use st.audio with JavaScript autoplay
            audio_code = f'<audio controls autoplay><source src="{preview_url}" type="audio/mp3"></audio>'
            st.markdown(audio_code, unsafe_allow_html=True)
        else:
            st.warning("No audio preview available for this track.")

    # Continue with predictions only if the Predict button is clicked
    if predict_button:
        ph.empty()
        progress_text = "The prediction is being calculated... Please wait."
        my_bar = st.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.015)
            my_bar.progress(percent_complete + 1, text=progress_text)
        time.sleep(0.5)
        my_bar.empty()

        # Get Track information and audio features for the selected track
        track_data, audio_features = get_track_info_and_features(selected_track_id, spotify_access_token)

        if track_data and audio_features:
            # Extract numerical features
            danceability = audio_features['danceability']
            energy = audio_features['energy']
            loudness = audio_features['loudness']
            speechiness = audio_features['speechiness']
            acousticness = audio_features['acousticness']
            liveness = audio_features['liveness']
            valence = audio_features['valence']
            tempo = audio_features['tempo']
            duration_ms = audio_features['duration_ms']
            instrumentalness = audio_features['instrumentalness']

            # Extract release year from release date
            release_date = track_data['album']['release_date']
            release_year = pd.to_datetime(release_date).year

            # Create a DataFrame for numerical features
            numeric_features_data = pd.DataFrame({
                'danceability': [danceability],
                'energy': [energy],
                'loudness': [loudness],
                'speechiness': [speechiness],
                'acousticness': [acousticness],
                'liveness': [liveness],
                'valence': [valence],
                'tempo': [tempo],
                'duration_ms': [duration_ms],
                'release_year': [release_year],
                'instrumentalness': [instrumentalness]
            })

            # Connect to the Spotify API to get the artist's genres
            artist_id = track_data['artists'][0]['id']
            artist_info_url = f'https://api.spotify.com/v1/artists/{artist_id}'
            artist_headers = {'Authorization': f'Bearer {spotify_access_token}'}

            try:
                artist_response = requests.get(artist_info_url, headers=artist_headers)
                artist_response.raise_for_status()
                artist_info = artist_response.json()

                # Extract the artist's genres
                artist_genres = artist_info.get('genres', [])  # List of artist genres

            except requests.exceptions.RequestException as e:
                st.error(f"Error getting artist information for artist ID {artist_id}: {e}")
                artist_genres = []

            # Create a DataFrame for known genres
            prediction_data = pd.DataFrame(columns=[
                'genres_Afro', 'genres_Alternative', 'genres_Ambient', 'genres_Blues',
                'genres_Christian & Gospel', 'genres_Classical', 'genres_Country',
                'genres_Dance/Electronic', 'genres_Folk & Acoustic', 'genres_Hip-Hop',
                'genres_Instrumental', 'genres_Indie', 'genres_Jazz', 'genres_K-Pop', 'genres_Latin',
                'genres_Metal', 'genres_Pop', 'genres_Punk', 'genres_R&B', 'genres_Rock',
                'genres_Soul'
            ])

            # Set 0 everywhere
            prediction_data.loc[0] = 0

            # Check if an artist genre matches the column names and set the corresponding column to 1
            for genre in artist_genres:
                lowercase_genre = genre.lower()

                # Search for exact matches in the normalized column names
                matching_columns = [col for col in prediction_data.columns if lowercase_genre == col.replace('genres_', '').lower()]

                # Also check for "hip hop" and "rap" as part of the genre name
                if "hip hop" in lowercase_genre or "rap" in lowercase_genre:
                    matching_columns.extend([col for col in prediction_data.columns if "hip-hop" in col.replace('genres_', '').lower()])

                # Check for K-Pop and Pop
                if lowercase_genre == "k-pop":
                    matching_columns.extend([col for col in prediction_data.columns if "k-pop" in col.replace('genres_', '').lower()])
                elif "pop" in lowercase_genre:
                    matching_columns.extend([col for col in prediction_data.columns if "pop" in col.replace('genres_', '').lower() and "k-pop" not in col.replace('genres_', '').lower()])

                if matching_columns:
                    # Set the first found column to 1
                    prediction_data.at[0, matching_columns[0]] = 1

                # Quick fix for presentation, REMOVE AFTER
                if lowercase_genre == "schlager":
                    prediction_data.loc[0] = 0

            # Load the saved scaler parameters
            with open('scaler.joblib', 'rb') as file:
                scaler = joblib.load(file)

            # Scale the numerical features
            scaled_numeric_features = scaler.transform(numeric_features_data)
            scaled_numeric_features_df = pd.DataFrame(scaled_numeric_features, columns=numeric_features_data.columns)

            # Here the merging happens
            final_data = pd.concat([scaled_numeric_features_df, prediction_data], axis=1)

            # Load the trained model
            with open('model1.pkl', 'rb') as file:
                trained_model = pickle.load(file)

            # Extract features for prediction
            features_for_prediction = final_data.values.reshape(1, -1)  # Reshape for a single observation

            # Perform the prediction
            predicted_score = trained_model.predict(features_for_prediction)

            # Load the second model
            loaded_model = pickle.load(open("monthly_listeners_model.pkl", "rb"))

            # Assumption: predicted_score is the predicted value
            pred_score = predicted_score

            # Perform the prediction
            predicted_monthly_listeners = loaded_model.predict([pred_score])

            # Calculate additional metrics based on the prediction
            predicted_monthly_streams = predicted_monthly_listeners * 2.5
            predicted_monthly_revenue = predicted_monthly_streams * 0.004

            # Now you have the predicted values that you can use in your main code
            st.markdown("<h1 style='text-align: center; color: white;'>Prediction results   </h1>", unsafe_allow_html=True)

            predicted_score_text = f"Predicted Popularity Score for the song: {int(round(predicted_score[0])):,}"
            predicted_monthly_revenue_text = f"Predicted Monthly Revenue for the artist of the song: ${round(predicted_monthly_revenue[0], 2):,}"

            # Create a container with a different background color
            with st.container():
                # Save artist name
                artist_name = track_data['artists'][0]['name']

                # Set the color of the score based on the condition
                score_color = "#1DB954" if predicted_score[0] >= 50 else "#FF0000"

                # Extract the text before the colon
                prefix_text = predicted_score_text.split(":")[0]

                # Extract the text after the colon
                suffix_text = predicted_score_text.split(":")[1]

                # Add the larger and more noticeable output
                st.markdown(
                    f"<p style='font-size: 26px; color: white; text-align: center;'>{prefix_text}:"
                    f"<span style='color: {score_color}; font-size: 26px; font-weight: bold;'>{suffix_text}</span></p>",
                    unsafe_allow_html=True
                )

                # Set the color of the revenue based on the condition
                revenue_color = "#1DB954" if predicted_monthly_revenue[0] >= 20000 else "#FF0000"

                # Extract the text before the colon
                prefix_revenue = predicted_monthly_revenue_text.split(":")[0]

                # Extract the text after the colon
                suffix_revenue = predicted_monthly_revenue_text.split(":")[1]

                st.markdown(
                    f"<p style='font-size: 26px; color: white; text-align: center;'>{prefix_revenue}: "
                    f"<span style='color: {revenue_color}; font-size: 26px; font-weight: bold;'>{suffix_revenue}</span></p>",
                    unsafe_allow_html=True
                )

                # Conditionally display additional text based on the revenue
                if predicted_score[0] < 50:
                    st.markdown(
                        f"<p style='font-size: 26px; color: #FF0000; text-align: center; font-weight: bold;'>The predicted score and monthly revenue is pretty low. Probably we should not sign {artist_name}</p>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<p style='font-size: 26px; color: #1DB954; text-align: center; font-weight: bold;'>It seems, {artist_name} might be a real talent. Let's get in touch with him/her!</p>",
                        unsafe_allow_html=True
                    )

            # Extract the track's preview URL
            preview_url = track_data.get('preview_url', None)

            if preview_url:
                st.subheader("Audio Preview:")

                # Use st.audio with JavaScript autoplay
                audio_code = f'<audio controls autoplay><source src="{preview_url}" type="audio/mp3"></audio>'
                st.markdown(audio_code, unsafe_allow_html=True)
            else:
                st.warning("No audio preview available for this track.")

        else:
            st.error("Error getting track information and audio features.")
