import re
import streamlit as st
from datetime import timedelta
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from openai import OpenAI

# =========================
# CONFIG (Streamlit Secrets)
# =========================

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# UTILITIES
# =========================

def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None


def format_timestamp(seconds):
    return str(timedelta(seconds=int(seconds)))


# =========================
# FETCH VIDEO METADATA
# =========================

def fetch_metadata(video_id):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    item = response["items"][0]

    return {
        "title": item["snippet"]["title"],
        "channel": item["snippet"]["channelTitle"],
        "published": item["snippet"]["publishedAt"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
    }


# =========================
# FETCH TRANSCRIPT
# =========================

def fetch_transcript(video_id):
    return YouTubeTranscriptApi.get_transcript(video_id)


# =========================
# CHUNK TRANSCRIPT
# =========================

def chunk_transcript(transcript, max_words=800):
    chunks = []
    current_chunk = []
    word_count = 0
    start_time = transcript[0]["start"]

    for entry in transcript:
        text = entry["text"]
        current_chunk.append(text)
        word_count += len(text.split())

        if word_count >= max_words:
            chunks.append({
                "text": " ".join(current_chunk),
                "start": start_time,
                "end": entry["start"]
            })
            current_chunk = []
            word_count = 0
            start_time = entry["start"]

    if current_chunk:
        chunks.append({
            "text": " ".join(current_chunk),
            "start": start_time,
            "end": transcript[-1]["start"]
        })

    return chunks


# =========================
# LLM SUMMARIZATION
# =========================

def summarize_text(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content


def generate_executive_summary(full_text):
    prompt = f"""
    Provide 5-8 concise executive bullet points.
    Do not hallucinate.
    Text:
    {full_text}
    """
    return summarize_text(prompt)


def generate_section_summary(text):
    prompt = f"""
    Summarize this section clearly in 4-5 lines.
    Stay factual.
    {text}
    """
    return summarize_text(prompt)


# =========================
# STREAMLIT UI
# =========================

st.set_page_config(layout="wide")
st.title("🎥 YouTube Video Summarizer")

url = st.text_input("Enter YouTube URL")

if url:
    video_id = extract_video_id(url)

    if video_id:
        try:
            metadata = fetch_metadata(video_id)
            transcript = fetch_transcript(video_id)
            chunks = chunk_transcript(transcript)
            full_text = " ".join([c["text"] for c in chunks])

            st.image(metadata["thumbnail"])
            st.header(metadata["title"])
            st.write(f"Channel: {metadata['channel']}")
            st.write(f"Published: {metadata['published']}")

            if st.button("Generate Summary"):

                with st.spinner("Generating summary..."):

                    exec_summary = generate_executive_summary(full_text)

                    st.subheader("Executive Summary")
                    st.write(exec_summary)

                    st.subheader("Section-wise Summary")

                    for chunk in chunks:
                        summary = generate_section_summary(chunk["text"])
                        st.markdown(
                            f"**{format_timestamp(chunk['start'])} - {format_timestamp(chunk['end'])}**"
                        )
                        st.write(summary)
                        st.divider()

        except Exception as e:
            st.error(f"Error: {str(e)}")
