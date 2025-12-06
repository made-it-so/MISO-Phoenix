import shutil
import time

while True:
    # Get disk usage statistics for the root filesystem
    total, used, free = shutil.disk_usage("/")

    # The print statement is included for completeness,
    # but its output will be redirected to /dev/null by the nohup command.
    print(
        f"Disk Usage: "
        f"Total: {total // (1024**3)} GB, "
        f"Used: {used // (1024**3)} GB, "
        f"Free: {free // (1024**3)} GB"
    )
    
    # Wait for 5 seconds before the next check
    time.sleep(5)
