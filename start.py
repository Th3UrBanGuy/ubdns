import subprocess`
import time`
import os`
import sys`
import re`
import threading`
import signal`
import json`

gunicorn_proc = None`
cloudflared_proc = None`
running = True`

def signal_handler(sig, frame):`
    global running`
    print("Received signal {}, shutting down...".format(sig))`
    running = False`
    if cloudflared_proc:`
        cloudflared_proc.terminate()`
    if gunicorn_proc:`
        gunicorn_proc.terminate()`
    sys.exit(0)`

signal.signal(signal.SIGTERM, signal_handler)`
signal.signal(signal.SIGINT, signal_handler)`

def start_gunicorn():`
    global gunicorn_proc`
    cmd = ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:8080", "app:app"]`
    gunicorn_proc = subprocess.Popen(cmd)`
    print("Gunicorn started with PID {}".format(gunicorn_proc.pid))`
    return gunicorn_proc`

def extract_tunnel_url(line):`
    if 'trycloudflare.com' in line:`
        match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)`;
        if match:`
            url = match.group(0)`
            with open('data/tunnel_url.txt', 'w') as f:`
                f.write(url)`
            with open('data/tunnel_info.json', 'w') as f:`
                json.dump({'url': url, 'updated_at': time.time()}, f)`;
            print("Tunnel URL: {}".format(url))`
            return url`
    return None`

def start_cloudflared():`
    global cloudflared_proc, running`
    
    # Get token from environment`
    token = os.getenv('CLOUDFLARE_TUNNEL_TOKEN')`
    
    while running:`
        print("Starting Cloudflare Tunnel...")`;
        
        if token:`
            # Use permanent tunnel with token`
            print("Using PERMANENT tunnel with token")`;
            cmd = ["cloudflared", "tunnel", "run", "--token", token, "--url", "http://localhost:8080"]`;
        else:`
            # Quick tunnel (temporary)`
            print("WARNING: Using QUICK tunnel (URL will change!)")`;
            cmd = ["cloudflared", "tunnel", "--url", "http://localhost:8080", 
                   "--logfile", "data/cloudflared.log"]`;
        
        cloudflared_proc = subprocess.Popen(`
            cmd,`
            stdout=subprocess.PIPE,`
            stderr=subprocess.STDOUT,`
            text=True`
        )`;
        print("Cloudflared started with PID {}".format(cloudflared_proc.pid))`;
        
        try:`
            for line in cloudflared_proc.stdout:`
                extract_tunnel_url(line)`;
                if not running:`
                    break`;
        except Exception as e:`
            print("Error: {}".format(e))`;
        
        retcode = cloudflared_proc.wait()`;
        print("Cloudflared exited with code {}".format(retcode))`;
        
        if not running:`
            break`;
            
        print("Restarting in 5 seconds...")`;
        time.sleep(5)`

if __name__ == '__main__':`
    gunicorn_proc = start_gunicorn()`
    
    cloudflared_thread = threading.Thread(target=start_cloudflared, daemon=True)`;
    cloudflared_thread.start()`;
    
    print("All services started.")`;
    
    try:`
        gunicorn_proc.wait()`;
    except KeyboardInterrupt:`
        print("Interrupted")`;
    
    running = False`;
    if cloudflared_proc:`
        cloudflared_proc.terminate()`;
    
    sys.exit(gunicorn_proc.returncode if gunicorn_proc else 0)`
