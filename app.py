import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_together import ChatTogether

import os
from dotenv import load_dotenv
load_dotenv()

SUMMARY_TEMPLATE = """You are a skilled content analyst. Create a clear, informative summary of the following video transcript in exactly 100-120 words. Focus on the main ideas, key insights, and core message.

Transcript:
{transcript}

Guidelines:
- Maintain objectivity
- Use clear, professional language
- Focus on key concepts and insights
- Stay within 100-120 words consisting of 2-3 points
- Use present tense
- Avoid redundancy

Summary:"""


ACTION_POINTS_TEMPLATE = """You are a practical implementation specialist. Based on the video transcript, identify specific, actionable takeaways that viewers can implement.

Transcript:
{transcript}

Create a list of implementation points following these guidelines:
- Focus on practical, actionable items
- Each point should start with an action verb
- Make points specific and measurable
- Include relevant context for implementation
- Prioritize high-impact actions
- List 3-5 points only
- Format each point as a clear instruction

Response Format: List the points with numbering.

Action Points:"""

class VideoAnalyzer:
    def __init__(self):
        self.llm = ChatTogether(
            api_key=os.getenv("TOGETHER_API_KEY"),
            temperature=0.0,
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
        )
        self.output_parser = CommaSeparatedListOutputParser()

    def analyze_transcript(self, transcript: str) -> dict:

        summary = self.llm.invoke(SUMMARY_TEMPLATE.format(transcript=transcript)).content
        action_points = self.llm.invoke(ACTION_POINTS_TEMPLATE.format(transcript=transcript)).content

        return {
            "summary": str(summary).strip(),
            "action_points": str(action_points).strip()
        }

    def extract_video_id(self, url: str) -> str:
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
            r'(?:embed\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_transcript(self, video_id: str) -> str:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return ' '.join(entry['text'] for entry in transcript)
        except Exception as e:
            st.error(f"Error fetching transcript: {str(e)}")
            return None

def main():
    st.title("Video Insight Generator")
    
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = VideoAnalyzer()

    video_url = st.text_input("Enter YouTube Video URL:")
    
    if video_url:
        video_id = st.session_state.analyzer.extract_video_id(video_url)
        
        if video_id:
            with st.spinner("Fetching transcript..."):
                transcript = st.session_state.analyzer.get_transcript(video_id)
            
            if transcript:
                with st.spinner("Analyzing content..."):
                    analysis = st.session_state.analyzer.analyze_transcript(transcript)
                    
                    st.subheader("Summary")
                    st.write(analysis["summary"])
                    
                    st.subheader("Action Points")
                    st.write(analysis["action_points"])
            else:
                st.warning("Could not fetch transcript for this video")
        else:
            st.error("Invalid YouTube URL")

if __name__ == "__main__":
    main()
    