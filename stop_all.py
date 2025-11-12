#!/usr/bin/env python

"""
Port Management Utility for Bench - SUPERVISOR AWARE + MEMORY SAFE VERSION
Handles supervisor-managed processes and prevents terminal/memory issues.
"""

import os, socket, errno, time, platform, subprocess, signal, sys, psutil

def get_port_suffix():
    """
    Reads the port suffix from redis_cache.conf file.
    """
    try:
        with open("./config/redis_cache.conf") as f:
            for line in f:
                if line.startswith('port'):
                    return line.split()[1][-1]
    except IOError:
        print('Error: Ensure this is running from your bench directory, ./config/redis_cache.conf not found.')
        exit(1)
    return '0'

def run_command(cmd, shell=False):
    """Run a command and return success status"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_memory_safety():
    """Check if system has enough memory to safely kill processes"""
    print("🧠 Checking memory status...")
    try:
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024 ** 3)
        used_percent = memory.percent
        
        print(f"   Available memory: {available_gb:.1f} GB")
        print(f"   Memory used: {used_percent:.1f}%")
        
        if available_gb < 0.5:  # Less than 500MB available
            print("⚠️  WARNING: Low memory available - killing processes may cause OOM")
            response = input("Continue anyway? (y/n): ")
            return response.lower() == 'y'
        elif used_percent > 90:
            print("⚠️  WARNING: High memory usage - system may kill processes")
            response = input("Continue anyway? (y/n): ")
            return response.lower() == 'y'
        else:
            print("✅ Memory status: OK")
            return True
    except:
        print("❓ Could not check memory status")
        return True

def get_safe_process_list():
    """Get list of processes to kill, excluding terminals and critical system processes"""
    print("🛡️  Building safe process list...")
    
    current_pid = os.getpid()
    parent_pid = os.getppid()
    
    # Get terminal-related PIDs to protect
    protected_pids = set()
    protected_names = set()
    
    # Protect current process chain
    protected_pids.add(current_pid)
    protected_pids.add(parent_pid)
    
    # Try to get grandparent and great-grandparent (terminal chain)
    try:
        # Get parent process info
        parent = psutil.Process(parent_pid)
        protected_pids.add(parent_pid)
        protected_names.add(parent.name())
        
        # Get grandparent
        grandparent = parent.parent()
        if grandparent:
            protected_pids.add(grandparent.pid)
            protected_names.add(grandparent.name())
            
            # Get great-grandparent
            great_grandparent = grandparent.parent()
            if great_grandparent:
                protected_pids.add(great_grandparent.pid)
                protected_names.add(great_grandparent.name())
    except:
        pass
    
    # Protect common terminal/shell processes
    protected_names.update(['bash', 'zsh', 'fish', 'sh', 'dash', 'tmux', 'screen', 'su', 'sudo'])
    
    print(f"   Protected PIDs: {protected_pids}")
    print(f"   Protected names: {protected_names}")
    
    return protected_pids, protected_names

def check_supervisor():
    """Check if supervisor is running and managing bench processes"""
    print("🔍 Checking supervisor status...")
    
    # Check if supervisor is running
    result = subprocess.run("sudo supervisorctl status", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("Supervisor is running:")
        print(result.stdout)
        return True
    else:
        print("Supervisor is not running or not accessible")
        return False

def stop_supervisor_processes():
    """Stop supervisor-managed bench processes"""
    print("🛑 Stopping supervisor processes...")
    
    # Stop all bench-related supervisor processes
    processes = [
        "bench-redis-cache", "bench-redis-queue", "bench-web", 
        "bench-worker", "bench-schedule", "bench-socketio"
    ]
    
    for process in processes:
        print(f"   Stopping {process}...")
        run_command(f"sudo supervisorctl stop {process}", shell=True)
        time.sleep(1)

def stop_supervisor_completely():
    """Stop supervisor service completely"""
    print("💀 Stopping supervisor service...")
    run_command("sudo systemctl stop supervisor", shell=True)
    run_command("sudo service supervisor stop", shell=True)
    time.sleep(2)

def kill_persistent_processes_safely(protected_pids, protected_names):
    """Kill processes that supervisor keeps restarting, but protect terminals"""
    print("🔫 Killing persistent processes (safely)...")
    
    # Define target patterns (bench processes only)
    target_patterns = [
        "frappe.utils.bench_helper",
        "redis-server.*conf",
        "node.*socketio",
        "gunicorn.*bench",
        "python.*bench"
    ]
    
    for pattern in target_patterns:
        print(f"   Targeting: {pattern}")
        
        # Use pgrep to get PIDs first
        result = subprocess.run(f"pgrep -f '{pattern}'", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid_str in pids:
                if pid_str:
                    try:
                        pid = int(pid_str)
                        # Check if PID is protected
                        if pid in protected_pids:
                            print(f"     Skipping protected PID: {pid}")
                            continue
                            
                        # Check process name
                        try:
                            proc = psutil.Process(pid)
                            if proc.name() in protected_names:
                                print(f"     Skipping protected process: {pid} ({proc.name()})")
                                continue
                        except:
                            pass
                            
                        # Safe to kill
                        print(f"     Killing PID: {pid}")
                        os.kill(pid, signal.SIGTERM)  # Try graceful first
                        
                    except (ValueError, ProcessLookupError, PermissionError):
                        pass
        
        time.sleep(0.5)
    
    # Wait for processes to terminate
    time.sleep(2)
    
    # Force kill any remaining target processes (still protecting terminals)
    for pattern in target_patterns:
        result = subprocess.run(f"pgrep -f '{pattern}'", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid_str in pids:
                if pid_str:
                    try:
                        pid = int(pid_str)
                        if pid not in protected_pids:
                            print(f"     Force killing PID: {pid}")
                            os.kill(pid, signal.SIGKILL)
                    except (ValueError, ProcessLookupError, PermissionError):
                        pass

def kill_other_bench_terminals():
    """Kill other bench-related terminal sessions but protect current one"""
    print("💻 Cleaning up other bench terminals...")
    
    current_pid = os.getpid()
    parent_pid = os.getppid()
    
    # Get current user
    current_user = os.getenv('USER')
    if not current_user:
        current_user = subprocess.run("whoami", shell=True, capture_output=True, text=True).stdout.strip()
    
    # Find other bench-related processes for current user
    patterns = [
        "bench start",
        "python.*stop.py",
        "frappe-bench/env/bin/python"
    ]
    
    for pattern in patterns:
        # Get PIDs of matching processes
        result = subprocess.run(f"pgrep -f '{pattern}'", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid_str in pids:
                if pid_str:
                    try:
                        pid = int(pid_str)
                        # Don't kill current process or its parent
                        if pid != current_pid and pid != parent_pid:
                            # Check if it's the same user
                            try:
                                proc = psutil.Process(pid)
                                if proc.username() == current_user:
                                    print(f"   Terminating other bench process: {pid}")
                                    os.kill(pid, signal.SIGTERM)
                            except:
                                print(f"   Terminating other bench process: {pid}")
                                os.kill(pid, signal.SIGTERM)
                    except (ValueError, ProcessLookupError, PermissionError):
                        pass
    
    time.sleep(1)

def main():
    """
    Main execution function - MEMORY SAFE + TERMINAL PROTECTED
    """
    print("🛑 Bench Stop Utility - MEMORY SAFE + TERMINAL PROTECTED")
    print("   This will protect your current terminal and check memory safety")
    
    # Step 0: Memory safety check
    if not check_memory_safety():
        print("❌ Aborting due to memory safety concerns")
        sys.exit(1)
    
    # Step 1: Get protected processes list
    protected_pids, protected_names = get_safe_process_list()
    
    port_suffix = get_port_suffix()
    ports = [f"{base_port}{port_suffix}" for base_port in [1100, 1200, 1300, 900, 800]]
    
    print(f"Target ports: {', '.join(ports)}")
    
    # Step 2: Check supervisor
    supervisor_detected = False
    if check_supervisor():
        supervisor_detected = True
        print("\n🚨 SUPERVISOR DETECTED - This is why processes keep restarting!")
        
        response = input("Stop supervisor-managed processes? (y/n): ")
        if response.lower() == 'y':
            stop_supervisor_processes()
            
            response = input("Stop supervisor service completely? (y/n): ")
            if response.lower() == 'y':
                stop_supervisor_completely()
    
    # Step 3: Kill other bench terminals (but protect current)
    response = input("Kill other bench terminal sessions? (y/n): ")
    if response.lower() == 'y':
        kill_other_bench_terminals()
    
    # Step 4: Kill persistent processes safely
    print("\n💀 Killing persistent processes (safely)...")
    kill_persistent_processes_safely(protected_pids, protected_names)
    
    # Step 5: Kill by ports
    print("\n🔪 Killing processes by port...")
    for port in ports:
        run_command(f"sudo fuser -k {port}/tcp 2>/dev/null", shell=True)
    
    # Step 6: Use bench stop
    print("\n🛑 Using bench stop...")
    run_command("bench stop", shell=True)
    
    time.sleep(3)
    
    # Final check
    print("\n🔍 Final status:")
    all_free = True
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", int(port)))
            sock.close()
            print(f"   ✅ Port {port} - FREE")
        except socket.error:
            print(f"   ❌ Port {port} - STILL IN USE")
            all_free = False
    
    if all_free:
        print("🎉 SUCCESS: All ports are free and your terminal is protected!")
    else:
        print("⚠️  Some ports are still in use")
    
    print(f"\n💡 You're still in: {os.getcwd()}")
    print("   Run: bench start")

if __name__ == '__main__':
    main()
