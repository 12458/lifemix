import os
import tempfile
import base64
import time
import json
import logging
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any, Optional
import typing_extensions as typing
import google.generativeai as genai


from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags
import googlemaps
from openai import OpenAI
from pydantic import BaseModel
import requests
import pycountry
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow CORS for all routes

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "mp4"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])


class VideoResponse(typing.TypedDict):
    location: str
    video_description: str
    mood_of_video: list[str]


class LyricsResponse(BaseModel):
    title: str
    lyrics: str
    genre_tags: List[str]
    song_bpm: int


class SongModel(BaseModel):
    id: str
    title: str
    lyric: str
    audio_url: str
    video_url: str
    created_at: datetime
    model_name: str
    status: str
    prompt: str
    type: str
    tags: str


# Initialize API clients
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

base_url = os.getenv("SUNO_API_BASE_URL", "http://localhost:3001")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def expand_language_code(code):
    try:
        language = pycountry.languages.get(alpha_2=code)
        return language.name
    except KeyError:
        return "English"


def custom_generate_audio(payload):
    url = f"{base_url}/api/custom_generate"
    # url = "http://localhost:3001/api/custom_generate"

    # Log the payload and URL
    logging.debug(f"Payload: {payload}")
    logging.debug(f"URL: {url}")

    response = requests.post(
        url, json=payload, headers={"Content-Type": "application/json"}
    )

    # Log the response
    logging.debug(f"Response: {response.json()}")

    # Check response code
    response.raise_for_status()

    # pydantic model
    ret = []
    for song in response.json():
        ret.append(SongModel.model_validate(song))
    return ret


def get_audio_information(audio_ids):
    url = f"{base_url}/api/get?ids={audio_ids}"

    # Log the URL
    logging.debug(f"URL: {url}")

    response = requests.get(url)

    # Log the response
    logging.debug(f"Response: {response.json()}")

    return response.json()[0]


def dms_to_dd(dms: tuple) -> float:
    degrees, minutes, seconds = dms
    return degrees + minutes / 60 + seconds / 3600


def get_exif_data(image_path: str) -> Dict[str, Any]:
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None

            decoded_exif = {
                ExifTags.TAGS.get(key, key): value for key, value in exif_data.items()
            }

            if "GPSInfo" in decoded_exif:
                gps_info = {
                    ExifTags.GPSTAGS.get(key, key): value
                    for key, value in decoded_exif["GPSInfo"].items()
                }
                decoded_exif["GPSInfo"] = gps_info

                if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                    lat = dms_to_dd(gps_info["GPSLatitude"])
                    lon = dms_to_dd(gps_info["GPSLongitude"])

                    lat *= -1 if gps_info.get("GPSLatitudeRef") == "S" else 1
                    lon *= -1 if gps_info.get("GPSLongitudeRef") == "W" else 1

                    decoded_exif["GPSInfo"]["GPSLatitude"] = lat
                    decoded_exif["GPSInfo"]["GPSLongitude"] = lon

            return decoded_exif
    except Exception as e:
        logging.error(f"Error reading EXIF data: {e}")
        return None


def get_relevant_exif_data(image_path: str) -> Dict[str, Any]:
    exif_data = get_exif_data(image_path)
    if exif_data:
        return {
            "Model": exif_data.get("Model"),
            "DateTime": exif_data.get("DateTime"),
            "Location": exif_data.get("GPSInfo"),
        }
    return None


def reverse_geocode(lat: float, lon: float) -> List[Dict[str, Any]]:
    logging.debug(f"Reverse geocoding: {lat}, {lon}")
    try:
        return gmaps.reverse_geocode((lat, lon))
    except Exception as e:
        logging.error(f"Error reverse geocoding: {e}")
        return None


def resize_and_encode_image(image_path: str, max_size: int = 1024) -> str:
    with Image.open(image_path) as img:
        # Resize image while maintaining aspect ratio
        img.thumbnail((max_size, max_size))

        # Convert to RGB if image is in CMYK mode
        if img.mode == "CMYK":
            img = img.convert("RGB")

        # Save the resized image to a BytesIO object
        buffered = BytesIO()
        img.save(buffered, format="JPEG")

        # Encode the image
        return base64.b64encode(buffered.getvalue()).decode("utf-8")


def process_images(directory: str) -> List[Dict[str, Any]]:
    image_data = []
    for file in os.listdir(directory):
        if file.lower().endswith((".jpeg", ".jpg")):
            image_path = os.path.join(directory, file)
            data = get_relevant_exif_data(image_path)
            if data and data.get("Location"):
                lat = data["Location"].get("GPSLatitude")
                lon = data["Location"].get("GPSLongitude")
                address = reverse_geocode(lat, lon)
                if address:
                    address_components = address[0].get("address_components", [])
                    location_str = ", ".join(
                        [comp["long_name"] for comp in address_components]
                    )
                    base64_image = resize_and_encode_image(image_path)
                    image_data.append(
                        {
                            "file": file,
                            "location": location_str,
                            "datetime": data.get("DateTime", "Unknown"),
                            "base64_image": base64_image,
                        }
                    )
    return image_data


def process_videos(directory: str) -> list[dict[str, Any]]:
    video_data = []
    for file in os.listdir(directory):
        logging.debug(f"Processing file: {file}")
        if file.lower().endswith(".mp4"):
            video_path = os.path.join(directory, file)
            logging.debug(f"Processing video: {video_path}")
            video_file = genai.upload_file(path=video_path)

            while video_file.state.name == "PROCESSING":
                logging.debug("Waiting for video to be processed.")
                time.sleep(10)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                raise ValueError(video_file.state.name)

            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = "Generate a description of the video, its mood and where the video takes place to your best guess."
            logging.debug(f"Generating description for video: {video_file.name}")
            result = model.generate_content(
                [prompt, video_file],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json", response_schema=VideoResponse
                ),
                request_options={"timeout": 600},
            )
            genai.delete_file(video_file.name)
            video_data.append(json.loads(result.text))
    
    return video_data


def generate_lyrics(image_data: List[Dict[str, Any]], genre_tags, language, video_data: Optional[list[dict[str, Any]]] = None) -> str:
    messages = [
        {
            "role": "system",
            "content": f"You are a talented songwriter. Generate song lyrics that capture the narrative of the series of images{" / video descriptions" if video_data is not None else ""} provided, considering their locations, mood and times.",
        }
    ]

    if genre_tags:
        messages.append(
            {
                "role": "user",
                "content": f"The song should have the following genre: {', '.join(genre_tags)}",
            }
        )

    if language:
        messages.append(
            {
                "role": "user",
                "content": f"The song should be in the following language: {expand_language_code(language)}",
            }
        )

    for idx, img in enumerate(image_data, 1):
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Image {idx}:\nLocation: {img['location']}\nDate/Time: {img['datetime']}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img['base64_image']}"
                        },
                    },
                ],
            }
        )
    
    if video_data:
        for idx, video in enumerate(video_data, 1):
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Video {idx}:\nLocation: {video['location']}\nDescription: {video['video_description']}\nMood: {', '.join(video['mood_of_video'])}",
                        },
                    ],
                }
            )
    

    try:
        logging.debug(f"Messages: {messages}")
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=messages,
            max_tokens=1000,
            response_format=LyricsResponse,
        )
        logging.debug(f"Lyrics response: {response}")
        return response.choices[0].message.parsed

    except Exception as e:
        logging.error(f"Error generating lyrics: {e}")
        return None


@app.route("/upload", methods=["POST"])
def upload_images():
    print("Received request")
    if "images" not in request.files:
        return jsonify({"error": "No images provided"}), 400

    files = request.files.getlist("images")
    logging.debug(f"Received files: {files}")

    if not files:
        return jsonify({"error": "No selected files"}), 400

    metadata = request.form.get("metadata")

    metadata_json = {}
    if metadata:
        metadata_json = json.loads(metadata)
        logging.debug(f"Received metadata: {metadata_json}")

    # Create a temporary directory to store uploaded images
    with tempfile.TemporaryDirectory() as temp_dir:
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(temp_dir, filename))
                logging.debug(f"Saved file: {filename}")

        # Process images
        logging.debug(f"Processing images in directory: {temp_dir}")
        image_data = process_images(temp_dir)
        video_data = process_videos(temp_dir)

        logging.debug(f"Image data len: {len(image_data)}")
        logging.debug(f"Video data len: {len(video_data)}")

        if not image_data and not video_data:
            return jsonify({"error": "No valid data found"}), 400

        # Generate lyrics
        lyrics_data = generate_lyrics(
            image_data, metadata_json.get("tags"), metadata_json.get("language"), video_data
        )

        if not lyrics_data:
            return jsonify({"error": "Failed to generate lyrics"}), 500

        # Generate audio from lyrics
        payload = {
            "prompt": lyrics_data.lyrics,
            "title": lyrics_data.title,
            "tags": (
                " ".join(
                    lyrics_data.genre_tags
                    if metadata_json.get("tags") is None
                    else metadata_json.get("tags")
                )
                + f" BPM: {lyrics_data.song_bpm if metadata_json.get("bpm") is None else metadata_json.get("bpm")}bpm"
                + f" Singer: {metadata_json.get('singer')}"
                if metadata_json.get("singer")
                and (metadata_json.get("singer") != "random")
                else (
                    "" + f" Language: {metadata_json.get('language')} "
                    if metadata_json.get("language")
                    else ""
                )
            ),
            "make_instrumental": False,
            "model": "chirp-v3-5",
            "wait_audio": False,
        }
        audio_response = custom_generate_audio(payload)
        logging.debug(f"Audio response: {audio_response}")

        # Poll for audio completion
        # Check schema for audio_info
        audio_id = audio_response[0].id
        audio_info = None
        while True:
            logging.debug(f"Polling for audio completion: {audio_id}")
            audio_info = get_audio_information(audio_id)
            if audio_info["status"] == "streaming":
                break
            time.sleep(10)

        return (
            jsonify(
                {
                    "id": audio_id,
                    "title": lyrics_data.title,
                    "lyrics": lyrics_data.lyrics,
                    "genre_tags": lyrics_data.genre_tags,
                    "song_bpm": (
                        lyrics_data.song_bpm
                        if metadata_json.get("bpm") is None
                        else metadata_json.get("bpm")
                    ),
                    "audio_url": audio_info["audio_url"],
                    "video_url": audio_info["video_url"],
                    "language": expand_language_code(metadata_json.get("language")),
                    "singer": metadata_json.get("singer", "Random"),
                }
            ),
            200,
        )


@app.route("/download", methods=["GET"])
def poll_ready_download():
    audio_id = request.args.get("id")
    audio_info = get_audio_information(audio_id)
    if audio_info["status"] != "complete":
        logging.debug(f"Audio not ready: {audio_id}, status: {audio_info['status']}")
        return jsonify({"ready": False}), 200
    return jsonify({"ready": True, "audio_url": audio_info["audio_url"]}), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(debug=True)
