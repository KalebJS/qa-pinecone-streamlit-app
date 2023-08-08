import json

import openai
import streamlit as st

from libraries import pinecone_client

# Options Sidebar
st.sidebar.title("Options")
st.sidebar.checkbox("Show formatted prompt", value=False, key="show_formatted_prompt")
st.sidebar.checkbox("Remember conversation", value=True, key="remember_conversation")
st.sidebar.number_input("Top k", value=10, key="top_k")
st.sidebar.number_input("Context padding", value=0, key="context_padding", min_value=0, max_value=5)

# Title
st.title("Chad from Gross Pointe")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Chat
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

with open("credentials.json", "r") as f:
    credentials = json.load(f)
openai.api_key = credentials["openai"]["api_key"]

conversation = []

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    try:
        formatted_prompt = pinecone_client.retrieve(
            prompt, top_k=st.session_state.top_k, context_padding=st.session_state.context_padding
        )
        if st.session_state.show_formatted_prompt:
            st.session_state.messages.append({"role": "assistant", "content": formatted_prompt})
            st.chat_message("assistant").write(formatted_prompt)
        conversation.append({"role": "user", "content": formatted_prompt})
        # share conversation and get response for formatted prompt
        if st.session_state.remember_conversation:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=conversation)
        else:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": formatted_prompt}]
            )
        msg = response.choices[0].message
        st.session_state.messages.append(msg)
        conversation.append(msg)
        st.chat_message("assistant").write(msg.content)
    except ValueError:
        message = {"role": "assistant", "content": "Sorry, I wasn't able to find any information on that question."}
        st.session_state.messages.append(message)
        conversation.append(message)
        st.chat_message("assistant").write(message["content"])
