"""
Math Explorer Agent - Web Server
Flask server providing REST API and SSE for interactive exploration
"""

import asyncio
import json
import queue
import threading
from datetime import datetime
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from agent import MathExplorerAgent
from config import MEMORY_SAVE_PATH

app = Flask(__name__, static_folder='website', static_url_path='/website')
CORS(app)

# Global state
agent_instance = None
event_queue = queue.Queue()
is_running = False
current_round = 0

# ================================
# Event Handlers
# ================================
def setup_event_handlers(agent):
    """Setup event handlers to push updates to SSE queue"""
    
    def on_action_start(data):
        event_queue.put({
            'type': 'action_start',
            'data': {
                'action_id': data.get('action_id', ''),
                'action_type': data.get('action_type', ''),
                'timestamp': datetime.now().isoformat()
            }
        })
    
    def on_action_complete(data):
        event_queue.put({
            'type': 'action_complete',
            'data': {
                'action_id': data.get('action_id', ''),
                'action_type': data.get('action_type', ''),
                'status': data.get('status', 'completed'),
                'timestamp': datetime.now().isoformat()
            }
        })
    
    def on_action_error(data):
        event_queue.put({
            'type': 'action_error',
            'data': {
                'action_id': data.get('action_id', ''),
                'error': data.get('error', 'Unknown error'),
                'timestamp': datetime.now().isoformat()
            }
        })
    
    def on_round_start(data):
        global current_round
        current_round = data.get('round', 0)
        event_queue.put({
            'type': 'round_start',
            'data': {
                'round': current_round,
                'actions_count': data.get('actions_count', 0),
                'timestamp': datetime.now().isoformat()
            }
        })
    
    def on_round_complete(data):
        event_queue.put({
            'type': 'round_complete',
            'data': {
                'round': data.get('round', 0),
                'timestamp': datetime.now().isoformat()
            }
        })
    
    def on_memory_saved(path):
        event_queue.put({
            'type': 'memory_saved',
            'data': {
                'path': path,
                'timestamp': datetime.now().isoformat()
            }
        })
    
    agent.on('action_start', on_action_start)
    agent.on('action_complete', on_action_complete)
    agent.on('action_error', on_action_error)
    agent.on('round_start', on_round_start)
    agent.on('round_complete', on_round_complete)
    agent.on('memory_saved', on_memory_saved)


# ================================
# Static File Serving
# ================================
@app.route('/')
def index():
    """Redirect to website"""
    return send_from_directory('website', 'index.html')

@app.route('/website/')
def website_index():
    """Serve website index"""
    return send_from_directory('website', 'index.html')

@app.route('/memory_snapshots/<path:filename>')
def serve_memory(filename):
    """Serve memory snapshot files"""
    return send_from_directory('memory_snapshots', filename)


# ================================
# API Endpoints
# ================================
@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current agent status"""
    global agent_instance, is_running, current_round
    
    has_agent = agent_instance is not None
    memory_summary = None
    
    if has_agent:
        memory = agent_instance.memory_manager.get_memory()
        memory_summary = {
            'objects': len(memory.objects),
            'concepts': len(memory.concepts),
            'directions': len(memory.directions),
            'conjectures': len(memory.conjectures),
            'lemmas': len(memory.lemmas)
        }
    
    return jsonify({
        'initialized': has_agent,
        'running': is_running,
        'current_round': current_round,
        'memory_summary': memory_summary
    })


@app.route('/api/start', methods=['POST'])
def start_exploration():
    """Initialize exploration from math text input"""
    global agent_instance, is_running
    
    if is_running:
        return jsonify({'error': 'Exploration is already running'}), 400
    
    data = request.get_json()
    math_text = data.get('text', '')
    
    if not math_text.strip():
        return jsonify({'error': 'Math text is required'}), 400
    
    try:
        # Create new agent instance
        agent_instance = MathExplorerAgent(save_path=MEMORY_SAVE_PATH)
        setup_event_handlers(agent_instance)
        
        # Initialize from input (runs Action 1: Parse Input)
        # Note: initialize_from_input is async, so we need to run it in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(agent_instance.initialize_from_input(math_text))
        loop.close()
        
        # Get initial memory state
        memory = agent_instance.memory_manager.get_memory()
        
        event_queue.put({
            'type': 'initialized',
            'data': {
                'success': True,
                'memory': memory.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
        })
        
        return jsonify({
            'success': True,
            'message': 'Exploration initialized',
            'memory': memory.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run', methods=['POST'])
def run_exploration():
    """Run exploration rounds"""
    global agent_instance, is_running
    
    if agent_instance is None:
        return jsonify({'error': 'Agent not initialized. Call /api/start first.'}), 400
    
    if is_running:
        return jsonify({'error': 'Exploration is already running'}), 400
    
    data = request.get_json() or {}
    rounds = data.get('rounds', 1)
    
    def run_async():
        global is_running
        is_running = True
        try:
            # Run the agent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                agent_instance.run(max_rounds=rounds, rounds_per_checkpoint=rounds + 1)
            )
            loop.close()
            
            event_queue.put({
                'type': 'exploration_complete',
                'data': {
                    'success': True,
                    'rounds_completed': rounds,
                    'timestamp': datetime.now().isoformat()
                }
            })
        except Exception as e:
            event_queue.put({
                'type': 'exploration_error',
                'data': {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            })
        finally:
            is_running = False
    
    # Run in background thread
    thread = threading.Thread(target=run_async)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Started {rounds} exploration round(s)'
    })


@app.route('/api/memory', methods=['GET'])
def get_memory():
    """Get current memory state"""
    global agent_instance
    
    if agent_instance is None:
        return jsonify({'error': 'Agent not initialized'}), 400
    
    memory = agent_instance.memory_manager.get_memory()
    return jsonify(memory.to_dict())


@app.route('/api/stop', methods=['POST'])
def stop_exploration():
    """Stop current exploration (sets flag for next checkpoint)"""
    global is_running
    
    # Note: This doesn't immediately stop, but will stop at next checkpoint
    is_running = False
    
    return jsonify({
        'success': True,
        'message': 'Stop requested (will stop at next checkpoint)'
    })


@app.route('/api/stream')
def event_stream():
    """SSE endpoint for real-time updates"""
    def generate():
        while True:
            try:
                # Wait for event with timeout
                event = event_queue.get(timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ================================
# Main
# ================================
if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    
    print("=" * 60)
    print("Math Explorer Agent - Web Server")
    print("=" * 60)
    print(f"Open http://localhost:{port}/website/ in your browser")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
