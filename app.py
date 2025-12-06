"""
Flask web application for Inwebstigate.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
from agent import WebInvestigationAgent
from config import Config
from logger import setup_logger
import os

logger = setup_logger('app')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inwebstigate-secret-key-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
current_agent = None
investigation_thread = None
is_investigating = False


def progress_callback(message: str, data: dict = None):
    """Callback to send progress updates via WebSocket."""
    socketio.emit('progress_update', {
        'message': message,
        'data': data
    })


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    return jsonify({
        'llm_provider': Config.LLM_PROVIDER,
        'ollama_model': Config.OLLAMA_MODEL,
        'groq_model': Config.GROQ_MODEL,
        'max_depth': Config.MAX_NAVIGATION_DEPTH,
        'has_groq_key': bool(Config.GROQ_API_KEY and Config.GROQ_API_KEY != 'your_groq_api_key_here')
    })


@socketio.on('start_investigation')
def handle_investigation(data):
    """Start a new investigation."""
    global current_agent, investigation_thread, is_investigating
    
    logger.info("=" * 60)
    logger.info("NEW INVESTIGATION REQUEST")
    logger.info("=" * 60)
    
    if is_investigating:
        logger.warning("Investigation already in progress, rejecting new request")
        emit('error', {'message': 'Investigation already in progress'})
        return
    
    query = data.get('query', '').strip()
    start_url = data.get('start_url', '').strip()
    llm_provider = data.get('llm_provider', Config.LLM_PROVIDER)
    max_depth = int(data.get('max_depth', Config.MAX_NAVIGATION_DEPTH))
    
    logger.info(f"Query: {query}")
    logger.info(f"Start URL: {start_url or 'None (will use search)'}")
    logger.info(f"LLM Provider: {llm_provider}")
    logger.info(f"Max Depth: {max_depth}")
    
    if not query:
        emit('error', {'message': 'Query is required'})
        return
    
    # Clean up start URL
    if start_url in ['http://', 'https://', '']:
        start_url = None
    
    is_investigating = True
    emit('investigation_started', {
        'query': query,
        'max_depth': max_depth,
        'llm_provider': llm_provider
    })
    
    def run_investigation():
        global current_agent, is_investigating
        try:
            logger.info("Creating investigation agent...")
            current_agent = WebInvestigationAgent(llm_provider, progress_callback)
            
            logger.info("Starting investigation...")
            final_answer = current_agent.investigate(query, start_url, max_depth)
            
            # Get investigation summary
            summary = current_agent.get_investigation_summary()
            logger.info(f"Investigation complete! Visited {summary['total_pages_visited']} pages")
            
            socketio.emit('investigation_complete', {
                'final_answer': final_answer,
                'summary': summary
            })
            
        except Exception as e:
            logger.error(f"Investigation failed: {e}", exc_info=True)
            socketio.emit('error', {'message': f'Investigation error: {str(e)}'})
        finally:
            is_investigating = False
            if current_agent:
                current_agent.cleanup()
                current_agent = None
    
    investigation_thread = threading.Thread(target=run_investigation, daemon=True)
    investigation_thread.start()


@socketio.on('stop_investigation')
def handle_stop():
    """Stop the current investigation."""
    global is_investigating, current_agent
    
    logger.warning("Stop investigation requested by user")
    
    if current_agent:
        logger.info("Signaling agent to stop...")
        current_agent.stop()  # Signal the agent to stop gracefully
        
        # Generate summary from what we have so far
        try:
            if current_agent.investigation_log:
                logger.info("Generating summary from collected data...")
                summary = current_agent.get_investigation_summary()
                # Get the query from the investigation somehow (we'll need to store it)
                emit('investigation_stopped', {
                    'message': 'Investigation stopped by user',
                    'summary': summary
                })
            else:
                emit('investigation_stopped', {'message': 'Investigation stopped before any data was collected'})
        except Exception as e:
            logger.error(f"Error generating summary on stop: {e}")
            emit('investigation_stopped', {'message': f'Investigation stopped: {str(e)}'})
    else:
        emit('investigation_stopped', {'message': 'No active investigation to stop'})
    
    is_investigating = False


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'message': 'Connected to Inwebstigate server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    global is_investigating, current_agent
    
    is_investigating = False
    if current_agent:
        current_agent.cleanup()
        current_agent = None


if __name__ == '__main__':
    print("🔍 Inwebstigate Web Application")
    print("=" * 50)
    print(f"LLM Provider: {Config.LLM_PROVIDER}")
    print(f"Model: {Config.OLLAMA_MODEL if Config.LLM_PROVIDER == 'ollama' else Config.GROQ_MODEL}")
    print(f"Max Navigation Depth: {Config.MAX_NAVIGATION_DEPTH}")
    print("=" * 50)
    print("\n🌐 Starting server at http://localhost:5001")
    print("📊 Open your browser and navigate to http://localhost:5001\n")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5001)

