#
# made by sgysh3nka
#
import ctypes
import tkinter as tk
from tkinter import filedialog
from functools import partial


class DLLInjector:
    def __init__(self, master):
        self.master = master
        master.title("sgysh3nka's injector")

        dll_label = tk.Label(master, text="DLL:")
        dll_label.grid(row=0, column=0, padx=5, pady=5, sticky="W")

        self.dll_entry = tk.Entry(master)
        self.dll_entry.grid(row=0, column=1, padx=5, pady=5)

        dll_button = tk.Button(master, text="Browse...", command=self.browse_dll)
        dll_button.grid(row=0, column=2, padx=5, pady=5)

        pid_label = tk.Label(master, text="Process ID:")
        pid_label.grid(row=1, column=0, padx=5, pady=5, sticky="W")

        self.pid_entry = tk.Entry(master)
        self.pid_entry.grid(row=1, column=1, padx=5, pady=5)

        pid_button = tk.Button(master, text="Select...", command=self.select_pid)
        pid_button.grid(row=1, column=2, padx=5, pady=5)

        inject_button = tk.Button(master, text="Inject", command=self.inject_dll)
        inject_button.grid(row=2, column=1, padx=5, pady=5)

        self.status_label = tk.Label(master, text="")
        self.status_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    def browse_dll(self):
        dll_filename = filedialog.askopenfilename()
        self.dll_entry.delete(0, tk.END)
        self.dll_entry.insert(0, dll_filename)

    def select_pid(self):
        target_pid = self.select_process()
        self.pid_entry.delete(0, tk.END)
        self.pid_entry.insert(0, target_pid)

    def select_process(self):
        target_pid = None
        target_process = None
        while not target_process:
            target_pid = self.prompt_for_pid()
            try:
                target_process = self.get_process_by_pid(target_pid)
            except Exception:
                self.display_error(f"Error: Process with PID {target_pid} could not be found.")
        self.display_status(f"Selected target process: {target_process}")
        return target_pid

    def prompt_for_pid(self):
        pid = tk.simpledialog.askinteger("Select Process", "Enter the Process ID of the target process:")
        return pid

    def get_process_by_pid(self, pid):
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not process_handle:
            raise Exception(f"Could not open process with PID {pid}")
        size = 256
        exe_path = ctypes.create_unicode_buffer(size)
        ctypes.windll.psapi.GetModuleFileNameExW(process_handle, None, exe_path, size)
        return exe_path.value

    def inject_dll(self):
        pid = self.pid_entry.get()
        dll_path = self.dll_entry.get()
        try:
            self.inject(pid, dll_path)
        except Exception as e:
            self.display_error(f"Error: {e}")

    def inject(self, pid, dll_path):
        PROCESS_CREATE_THREAD = 0x0002
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_OPERATION = 0x0008
        PROCESS_VM_WRITE = 0x0020
        PROCESS_VM_READ = 0x0010
        kernel32_handle = ctypes.windll.kernel32._handle
        kernel32_address = ctypes.windll.kernel32.GetModuleHandleA(b"kernel32.dll")
        load_library_address = ctypes.windll.kernel32.GetProcAddress(kernel32_address, b"LoadLibraryA")
        process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
                                                            PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_VM_READ,
                                                            False,
                                                            int(pid))
        if not process_handle:
            raise Exception(f"Could not open process with PID {pid}")
        dll_path_buffer = ctypes.c_char_p(dll_path.encode("utf-8"))
        dll_path_size = len(dll_path) + 1
        memory_allocation_address = ctypes.windll.kernel32.VirtualAllocEx(process_handle,
                                                                           None,
                                                                           dll_path_size,
                                                                           0x1000 | 0x2000,
                                                                           0x40)
        ctypes.windll.kernel32.WriteProcessMemory(process_handle,
                                                  memory_allocation_address,
                                                  dll_path_buffer,
                                                  dll_path_size,
                                                  None)
        ctypes.windll.kernel32.CreateRemoteThread(process_handle,
                                                   None,
                                                   0,
                                                   load_library_address,
                                                   memory_allocation_address,
                                                   0,
                                                   None)

        h_module_snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(0x00000008, int(pid))
        module_entry = ctypes.Structure()
        module_entry.dwSize = ctypes.sizeof(module_entry)
        module_list = []
        if ctypes.windll.kernel32.Module32First(h_module_snapshot, ctypes.pointer(module_entry)):
            while ctypes.windll.kernel32.Module32Next(h_module_snapshot, ctypes.pointer(module_entry)):
                module_list.append(module_entry.szModule.decode())
        ctypes.windll.kernel32.CloseHandle(h_module_snapshot)
        if os.path.basename(dll_path) not in module_list:
            raise Exception(f"Failed to inject {dll_path} into process with PID {pid}")

        self.display_status(f"Injected {dll_path} into process with PID {pid}")

    def display_status(self, message):
        self.status_label.config(text=message, fg="green")

    def display_error(self, message):
        self.status_label.config(text=message, fg="red")


if __name__ == '__main__':
    root = tk.Tk()
    dll_injector = DLLInjector(root)
    root.mainloop()
