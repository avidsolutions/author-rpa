# Azure App Service entry point
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import full RPA Flask app
    from web.app import app
except Exception as e:
    # Fallback minimal app if imports fail
    from flask import Flask
    app = Flask(__name__)

    error_msg = str(e)

    @app.route('/')
    def home():
        return f'''
        <h1>RPA Framework</h1>
        <p style="color: red;">Import Error: {error_msg}</p>
        <p>The full application could not be loaded. Check dependencies.</p>
        '''

    @app.route('/health')
    def health():
        return 'OK'

if __name__ == '__main__':
    app.run()
