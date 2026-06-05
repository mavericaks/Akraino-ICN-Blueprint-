import paramiko
import sys
import time

def run_ssh_command(host, user, password, command):
    print(f"Connecting to {host}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=host, username=user, password=password, timeout=10)
        print(f"Running command: {command}")
        
        # Use invoke_shell to get a pty, which helps with some commands and sudo
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        # If it's a sudo command that might need password, provide it
        if "sudo" in command:
            stdin.write(password + "\n")
            stdin.flush()
        
        exit_status = stdout.channel.recv_exit_status()
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        print(f"Exit status: {exit_status}")
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        print("--- Output ---")
        print(output)
        if error:
            print("--- Error ---")
            print(error)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ssh_runner.py 'command'")
        sys.exit(1)
        
    cmd = sys.argv[1]
    run_ssh_command("192.168.137.155", "icn", "123", cmd)
