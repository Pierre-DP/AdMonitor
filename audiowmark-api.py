from flask import Flask, request, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'audiowmark-api'})

@app.route('/add', methods=['POST'])
def add_watermark():
    """Add watermark to audio file"""
    try:
        data = request.json
        audio_bytes = bytes(data['audio'])
        watermark_id = data['watermarkId']
        strength = data.get('strength', 10)
        
        # Write audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as input_file:
            input_file.write(audio_bytes)
            input_path = input_file.name
        
        # Output file
        output_path = input_path.replace('.wav', '_watermarked.wav')
        
        # Run audiowmark
        cmd = [
            'audiowmark', 'add',
            input_path,
            output_path,
            watermark_id,
            '--strength', str(strength)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Audiowmark failed: {result.stderr}")
        
        # Read watermarked audio
        with open(output_path, 'rb') as f:
            watermarked_audio = f.read()
        
        # Cleanup
        os.unlink(input_path)
        os.unlink(output_path)
        
        return jsonify({
            'success': True,
            'audio': list(watermarked_audio)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/detect', methods=['POST'])
def detect_watermark():
    """Detect watermark in audio"""
    try:
        data = request.json
        audio_bytes = bytes(data['audio'])
        
        # Write audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as input_file:
            input_file.write(audio_bytes)
            input_path = input_file.name
        
        # Run audiowmark detection
        cmd = ['audiowmark', 'get', input_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse output
        watermark_found = result.returncode == 0
        watermark_id = None
        confidence = 0.0
        
        if watermark_found:
            # Parse audiowmark output for watermark ID and quality
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'pattern' in line.lower():
                    watermark_id = line.split()[-1]
                if 'quality' in line.lower():
                    try:
                        confidence = float(line.split()[-1])
                    except:
                        confidence = 80.0
        
        # Cleanup
        os.unlink(input_path)
        
        return jsonify({
            'watermarkFound': watermark_found,
            'watermarkId': watermark_id,
            'confidence': confidence
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
