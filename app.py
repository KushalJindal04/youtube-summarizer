import streamlit as st
import random

# Page config
st.set_page_config(page_title="Simple AI App", page_icon="🤖")

st.title("🤖 Simple AI App (No API Keys Required)")
st.write("This app works completely offline without any API keys.")

# User input
user_input = st.text_input("Enter your question:")

# Simple AI-like responses
responses = [
    "That's an interesting question!",
    "Let me think about that...",
    "Here’s something you can consider.",
    "Great question! Here's a simple explanation.",
    "I like the way you're thinking!"
]

if st.button("Generate Response"):
    if user_input:
        st.success(random.choice(responses))
        st.write("You asked:", user_input)
    else:
        st.warning("Please enter a question first.")
