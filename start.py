import subprocess
import time
import os
import sys
import re
import threading
import signal
import json

# Global process trackers
gunicorn_proc = None
cloudflared_proc = None
running = True

def signal_handler(sig, frame):
    global running
    print(f"Received signal {sig}, shutting down...")
    running = False
    if cloudflared_proc:
        cloudflared_proc.terminate()
    if gunicorn_proc:
        gunicorn_proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def start_gunicorn():
    global gunicorn_proc
    cmd = ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:8080", "app:app"]
    gunicorn_proc = subprocess.Popen(cmd)
    print(f"Gunicorn started with PID {gunicorn_proc.pid}")
    return gunicorn_proc

def extract_tunnel_url(line):
    """Extract tunnel URL from cloudflared output"""
    if 'trycloudflare.com' in line:
        match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
        if match:
            url = match.group(0)
            # Save URL to files
            with open('data/tunnel_url.txt', 'w') as f:
                f.write(url)
            with open('data/tunnel_info.json', 'w') as f:
                json.dump({'url': url, 'updated_at': time.time()}, f)
            print(f"✅ Tunnel URL: {url}")
            return url
    return None

def start_cloudflared():
    global cloudflared_proc, running
    
    # FORCE permanent tunnel - no fallback to quick tunnel!
    tunnel_id = os.getenv('CLOUDFLARE_TUNNEL_ID')
    tunnel_token = os.getenv('CLOUDFLARE_TUNNEL_TOKEN')
    
    if not tunnel_id or not tunnel_token:
        print("ERROR: CLOUDFLARE_TUNNEL_ID and CLOUDFLARE_TUNNEL_TOKEN must be set!")
        print("Container will not start Cloudflared!")
        return
    
    print(f"Using PERMANENT tunnel ID: {tunnel_id}")
    print(f"Token length: {len(tunnel_token)}")
    
    while running:
        print("Starting Cloudflare Tunnel (PERMANENT)...")
        
        # Use tunnel run with token (permanent tunnel)
        cmd = ["cloudflared", "tunnel", "run", "--token", tunnel_token]
        
        cloudflared_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(f"Cloudflared started with PID {cloudflared_proc.pid}")
        
        # Read output to capture URL
        url_found = False
        try:
            for line in cloudflared_proc.stdout:
                extract_tunnel_url(line)
                if 'trycloudflare.com' in line:
                    url_found = True
                if not running:
                    break
        except Exception as e:
            print(f"Error reading cloudflared output: {e}")
        
        # Wait for process to finish
        retcode = cloudflared_proc.wait()
        print(f"Cloudflared exited with code {retcode}")
        
        if not running:
            break
            
        print("Restarting Cloudflare Tunnel in 5 seconds...")
        time.sleep(5)

if __name__ == '__main__':
    # Start gunicorn
    gunicorn_proc = start_gunicorn()
    
    # Start cloudflared in a separate thread
    cloudflared_thread = threading.Thread(target=start_cloudflared, daemon=True)
    cloudflared_thread.start()
    
    print("All services started. Waiting for processes...")
    
    # Wait for gunicorn (main process)
    try:
        gunicorn_proc.wait()
    except KeyboardInterrupt:
        print("Interrupted")
    
    running = False
    if cloudflared_proc:
        cloudflared_proc.terminate()
    
    sys.exit(gunicorn_proc.returncode if gunicorn_proc else 0)
