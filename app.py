# app.py - Main Flask application configuration and routes
import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from caption_service import extract_captions, format_captions, validate_youtube_url
from werkzeug.middleware.proxy_fix import ProxyFix

print('running...')

# Create and configure the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Enable CORS for all routes to allow frontend integration
CORS(app)

# Configure logging
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')

@app.route('/docs')
def documentation():
    """Render the API documentation page."""
    return render_template('documentation.html')

@app.route('/api/extract-captions', methods=['POST'])
def get_captions():
    """
    API endpoint to extract and format YouTube video captions.
    
    Expects a JSON payload with a 'url' field containing a valid YouTube URL.
    Returns formatted captions or appropriate error messages.
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing YouTube URL',
                'message': 'Please provide a valid YouTube URL in the request body'
            }), 400
        
        url = data['url']
        logger.debug(f"Received request to extract captions for URL: {url}")
        
        # Validate the YouTube URL
        if not validate_youtube_url(url):
            return jsonify({
                'error': 'Invalid YouTube URL',
                'message': 'The provided URL does not appear to be a valid YouTube video URL'
            }), 400
        
        # Extract captions from the YouTube video
        raw_captions = extract_captions(url)
        
        if not raw_captions:
            return jsonify({
                'error': 'Captions unavailable',
                'message': 'No captions/subtitles available for this video or they are disabled'
            }), 404
        
        # Format the raw captions for readability
        formatted_text = format_captions(raw_captions)
        
        # Return the formatted captions
        return jsonify({
            'success': True,
            'captions': formatted_text,
            'videoUrl': url,
            'length': len(formatted_text)
        })
        
    except Exception as e:
        logger.error(f"Error processing caption request: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Server error',
            'message': f'An error occurred while processing the captions: {str(e)}'
        }), 500

# Error handlers for common HTTP errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found on this server'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The method is not allowed for the requested URL'
    }), 405

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'error': 'Server error',
        'message': 'An internal server error occurred'
    }), 500

if __name__ == '__main__':
    app.run(debug=True)