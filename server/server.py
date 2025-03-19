from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder='../client/build', static_url_path='/')

@app.route('/api/infer', methods=['POST'])
def infer():
    # Your fuzzy logic goes here later!
    return jsonify({'result': 'test response'})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run()
