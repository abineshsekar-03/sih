import os
import sys
import requests
import time

def check_backend():
    print("Checking backend API...", end=" ")
    try:
        response = requests.get("http://localhost:8000/api/system-status")
        if response.status_code == 200:
            print("OK")
            return True
        else:
            print(f"FAILED (Status {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("FAILED (Connection Refused - Is backend running?)")
        return False

def check_frontend():
    print("Checking frontend server...", end=" ")
    try:
        response = requests.get("http://localhost:5173")
        if response.status_code == 200:
            print("OK")
            return True
        else:
            print(f"FAILED (Status {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("FAILED (Connection Refused - Is frontend running?)")
        return False

if __name__ == "__main__":
    print("========================================")
    print("SIH26073 SYSTEM CHECK")
    print("========================================")
    
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    print("========================================")
    if backend_ok and frontend_ok:
        print("ALL SYSTEM CHECKS PASSED")
        sys.exit(0)
    else:
        print("SYSTEM CHECK FAILED")
        sys.exit(1)
