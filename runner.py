from os import system
from time import sleep

while True:
    print("[Runner] Starting service.py")
    system("python service.py")
    print("[Runner] Restarting...")
    sleep(0.2)  # 200ms to CTR+C twice
