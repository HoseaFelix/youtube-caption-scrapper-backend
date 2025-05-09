# caption_service.py - Service for YouTube caption extraction and processing
import re
import logging
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

# Configure logging
logger = logging.getLogger(__name__)

def validate_youtube_url(url):
    """
    Validate if the provided URL is a valid YouTube video URL.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if valid YouTube URL, False otherwise
    """
    if not url:
        return False
    
    # Common YouTube URL patterns
    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(www\.)?youtu\.be/[\w-]+'
    ]
    
    # Check if URL matches any YouTube pattern
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False

def extract_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    
    Args:
        url (str): The YouTube URL
        
    Returns:
        str: The YouTube video ID or None if not found
    """
    parsed_url = urlparse(url)
    
    # Handle youtu.be format
    if 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')
    
    # Handle youtube.com format
    if 'youtube.com' in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        if 'v' in query_params:
            return query_params['v'][0]
    
    return None

def extract_captions(url):
    """
    Extract captions/subtitles from a YouTube video.
    
    Args:
        url (str): The YouTube video URL
        
    Returns:
        list: A list of caption segments or None if not available
    """
    try:
        video_id = extract_video_id(url)
        
        if not video_id:
            logger.warning(f"Could not extract video ID from URL: {url}")
            return None
        
        logger.debug(f"Extracting captions for video ID: {video_id}")
        
        # Get the available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            # If English not available, get the first available transcript
            transcript = transcript_list.find_transcript(['en-US', 'en-GB'])
            
        # Get the transcript data
        caption_data = transcript.fetch()
        return caption_data
        
    except NoTranscriptFound:
        logger.warning(f"No transcript found for video: {url}")
        return None
    except TranscriptsDisabled:
        logger.warning(f"Transcripts are disabled for video: {url}")
        return None
    except VideoUnavailable:
        logger.warning(f"Video unavailable: {url}")
        return None
    except Exception as e:
        logger.error(f"Error extracting captions: {str(e)}")
        return None

def format_captions(caption_data):
    """
    Process and format raw caption data into readable text.
    
    Args:
        caption_data (list): List of caption segments from YouTube
        
    Returns:
        str: Formatted text for readability
    """
    if not caption_data:
        return ""
    
    # Extract text from each caption segment
    # The YouTube API returns objects with attributes, not dictionaries
    try:
        # Try accessing as dictionary first (for backwards compatibility)
        caption_texts = [segment['text'] for segment in caption_data]
    except (TypeError, KeyError):
        # If that fails, try accessing as object attributes
        try:
            caption_texts = [segment.text for segment in caption_data]
        except AttributeError:
            # If both methods fail, log the error and return empty string
            logger.error(f"Unable to extract text from captions. Type: {type(caption_data)}")
            if caption_data:
                logger.error(f"First item type: {type(caption_data[0])}")
            return "Error: Unable to process captions from this video. Please try another video."
    
    # Join all texts into a single string
    raw_text = ' '.join(caption_texts)
    
    # Clean up common formatting issues
    cleaned_text = raw_text
    
    # Remove redundant newlines and spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    # Fix sentence breaks (ensure proper spacing after periods)
    cleaned_text = re.sub(r'\.(?=[A-Z])', '. ', cleaned_text)
    
    # Add paragraph breaks at natural points (every ~5-7 sentences)
    sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    paragraphs = []
    
    for i in range(0, len(sentences), 5):
        paragraph = ' '.join(sentences[i:i+5])
        if paragraph:
            paragraphs.append(paragraph)
    
    formatted_text = '\n\n'.join(paragraphs)
    
    return formatted_text