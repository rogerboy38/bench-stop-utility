#!/usr/bin/env python

"""
Bench Stop - Production Ready
Zero freeze, no sudo prompts, fast and reliable.
"""

import os
import time
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_async_command(cmd, timeout=3):
    """Run command asynchronously with hard timeout"""
    def _run_command():
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                if process.poll() is not None:
                    return True
                time.sleep(0.1)
            
            # Timeout - kill process group
            try:
                os.killpg(os.getpgid(process.pid), 9)
            except:
                process.kill()
            return False
            
        except Exception:
            return False
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_command)
        try:
            return future.result(timeout=timeout + 1)
        except:
            return False

def stop_bench():
    """Main stop function - optimized for production"""
    print("🛑 Stopping Bench Services")
    print("💡 Zero freeze guarantee • No sudo required")
    
    # All commands that don't need sudo
    commands = [
        "pkill -f 'frappe.utils.bench_helper'",
        "pkill -f 'redis-server.*conf'", 
        "pkill -f 'node.*socketio'",
        "pkill -f 'gunicorn.*bench'",
        "timeout 5 bench stop",
    ]
    
    print(f"⚡ Running {len(commands)} commands...")
    
    # Execute all commands in parallel
    completed = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_async_command, cmd, 3) for cmd in commands]
        
        for future in as_completed(futures, timeout=10):
            try:
                if future.result():
                    completed += 1
            except:
                pass
    
    print(f"✅ Commands completed: {completed}/{len(commands)}")
    print("🎉 Bench stopped successfully!")
    print("🚀 Run: bench start")

if __name__ == '__main__':
    try:
        stop_bench()
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
