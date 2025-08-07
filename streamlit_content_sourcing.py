#!/usr/bin/env python3
"""
Streamlit UI for Content Sourcing Agent
"""

import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv
from config_updated import get_config, AgentConfig  # Import from config.py
from agant_updated import ContentSourcingAgent  # Assuming agant_updated.py is content_sourcing_agent.py
from typing import List, Dict

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(page_title="Content Sourcing Agent Dashboard", layout="wide")

# Title and timestamp
st.title("Content Sourcing Agent Dashboard")
st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")

# Sidebar for navigation and inputs
st.sidebar.header("Dashboard Controls")
selected_view = st.sidebar.selectbox("Select View", ["Overview", "Content"])
query = st.sidebar.text_input("Enter Query", value=os.getenv('TEST_QUERY', 'artificial intelligence in automotive systems'))

# Safely get STATIC_SOURCES
config = get_config()
default_sources = getattr(config, 'STATIC_SOURCES', [
    "https://en.wikipedia.org/wiki/AUTOSAR",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://arxiv.org/abs/2303.08774",
    "https://en.wikipedia.org/wiki/Electronic_control_unit",
    "https://www.sae.org/standards/content/j1939_201808/",
    "https://arxiv.org/abs/2006.06068"
])
sources_input = st.sidebar.text_area("Enter Sources (comma-separated URLs)", value=os.getenv('TEST_SOURCES', ','.join(default_sources)))
sources = [url.strip() for url in sources_input.split(',') if url.strip()]
run_button = st.sidebar.button("Run Content Sourcing Agent")

# Initialize or reuse agent
if 'agent' not in st.session_state:
    st.session_state.results = None
    st.session_state.stored_content = []
    try:
        st.session_state.agent = ContentSourcingAgent(
            api_key=getattr(config, 'GROQ_API_KEY', ''),
            model=getattr(config, 'LLM_MODEL', 'gemma2-9b-it'),
            base_url=getattr(config, 'LLM_BASE_URL', 'https://api.groq.com/'),
            max_tokens=getattr(config, 'MAX_TOKENS', 500)
        )
    except Exception as e:
        st.error(f"Failed to initialize ContentSourcingAgent: {e}")
        st.session_state.agent = None

agent = st.session_state.agent

# Run agent when button is clicked
if run_button and agent:
    with st.spinner("Processing content..."):
        try:
            result = agent.run(query, sources)
            st.session_state.results = result
            st.session_state.stored_content = agent.get_all_stored_content()
            st.success("Content sourcing completed!")
        except Exception as e:
            st.error(f"Error running agent: {e}")
            st.session_state.results = None
            st.session_state.stored_content = []

# Display views based on selection
if selected_view == "Overview":
    st.header("Execution Summary")
    if st.session_state.results is not None:
        result = st.session_state.results
        st.write(f"**Query:** {result.get('query', 'Unknown')}")
        st.write(f"**Sources Processed:** {len(result.get('sources', []))}")
        st.write(f"**Content Items Fetched:** {len(result.get('raw_content', []))}")
        st.write(f"**Content Items Processed:** {len(result.get('processed_content', []))}")
        st.write(f"**Content Items Stored:** {len(result.get('stored_content', []))}")
        st.write(f"**Errors Encountered:** {len(result.get('errors', []))}")
        if result.get('errors'):
            st.subheader("Errors")
            for error in result.get('errors', []):
                st.error(error)
    else:
        st.write("No execution results yet. Run the agent to process content.")

    # Display configuration summary
    st.subheader("Agent Configuration")
    st.write(f"**LLM Model:** {getattr(config, 'LLM_MODEL', 'Unknown')}")
    st.write(f"**Quality Threshold:** {getattr(config, 'QUALITY_THRESHOLD', 'Unknown')}")
    st.write(f"**Max Sources:** {getattr(config, 'MAX_SOURCES', 'Unknown')}")
    st.write(f"**Content Chunk Size:** {getattr(config, 'CONTENT_CHUNK_SIZE', 'Unknown')}")
    st.write(f"**Max Tokens:** {getattr(config, 'MAX_TOKENS', 'Unknown')}")
    config_issues = config.validate_config()
    if config_issues:
        st.warning("Configuration Issues:")
        for issue in config_issues:
            st.write(f"- {issue}")
    else:
        st.write("✅ Configuration is valid")

elif selected_view == "Content":
    st.header("Processed Content")
    if st.session_state.stored_content:
        for i, content in enumerate(st.session_state.stored_content, 1):
            with st.expander(f"{i}. {content['title']}"):
                st.write(f"**Category:** {content['category']}")
                st.write(f"**Tags:** {', '.join(content['tags'])}")
                st.write(f"**Quality Score:** {content['quality_score']:.2f}")
                st.write(f"**Bloom Level:** {content.get('bloom_level', 'Unknown')}")
                st.write(f"**Source URL:** {content['source_url']}")
                st.write(f"**Word Count:** {content['metadata']['word_count']}")
                content_preview = content['content'][:200] + "..." if len(content['content']) > 200 else content['content']
                st.write(f"**Preview:** {content_preview}")
    else:
        st.write("No content stored yet. Run the agent to process content.")

# Add a footer
st.sidebar.text("Powered by xAI Grok 3")
