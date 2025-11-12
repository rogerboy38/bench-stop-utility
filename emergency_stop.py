#!/usr/bin/env python

"""
Emergency Bench Stop - With Sudo Warning
Clearly indicates when sudo is needed.
"""

import os
import time
import subprocess
import sys

def run_never_freezes(cmd, max_time=2):
    """Run command that absolutely cannot freeze"""
    try:
        full_cmd = f"timeout -s KILL {max_time} {cmd} 2>/dev/null"
        process = subprocess.Popen(full_cmd, shell=True)
        time.sleep(0.1)
        return True
    except:
        return False

def main():
    print("🚨 EMERGENCY BENCH STOP")
    print("💥 Hard kill timeouts • Zero freeze guaranteed")
    print("⚠️  Use only when other methods fail")
    print("🔐 Some commands require sudo (will prompt)")
    
    # Separate sudo and non-sudo commands
    non_sudo_commands = [
        "pkill -9 -f 'frappe.utils.bench_helper'",
        "pkill -9 -f 'redis-server'",
        "pkill -9 -f 'node'",
        "pkill -9 -f 'gunicorn'",
        "timeout -s KILL 3 bench stop",
    ]
    
    sudo_commands = [
        "sudo supervisorctl stop all",
        "sudo systemctl stop supervisor", 
        "sudo fuser -k 11006/tcp",
        "sudo fuser -k 12006/tcp",
        "sudo fuser -k 13006/tcp", 
        "sudo fuser -k 9006/tcp",
        "sudo fuser -k 8006/tcp",
    ]
    
    print("\n🔧 Running non-sudo commands...")
    for i, cmd in enumerate(non_sudo_commands, 1):
        print(f"   {i}. {cmd.split()[0]}...")
        run_never_freezes(cmd, 2)
    
    print("\n🔐 Running sudo commands (may prompt for password)...")
    for i, cmd in enumerate(sudo_commands, len(non_sudo_commands) + 1):
        print(f"   {i}. {cmd.split()[0]}...")
        run_never_freezes(cmd, 2)
    
    print(f"\n✅ Sent {len(non_sudo_commands) + len(sudo_commands)} commands")
    print("🛡️  Terminal is safe! Run: bench start")

if __name__ == '__main__':
    main()
