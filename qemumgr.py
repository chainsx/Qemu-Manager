import os
import tkinter as tk
import atexit
from subprocess import PIPE
from subprocess import Popen, CalledProcessError
from tkinter.messagebox import showinfo as alert
from tkinter.messagebox import askyesno as confirm
from ttkthemes import ThemedTk
from tkinter import ttk

qemu_process = None
qemu_type_box = None
cdrom_path = None

class Manager:
    def __init__(self) -> None:
        self.root = ThemedTk()
        self.root.title("QEMU Manager")
        self.root.geometry("600x600")
        self.root.wm_resizable(False, False)

        self.root.style = ttk.Style()
        self.root.style.theme_use("arc")
        self.root.style.configure("raised.TButton", borderwidth=1)

        # Variables
        self.qemu_kill_on_exit = tk.BooleanVar()
        self.qemu_kill_on_exit.set(True)

        self.qemu_sdl_window = tk.BooleanVar()
        self.qemu_sdl_window.set(False)

        self.qemu_use_haxm = tk.BooleanVar()
        self.qemu_use_haxm.set(True)

        self.qemu_finish_inst = tk.BooleanVar()
        self.qemu_finish_inst.set(True)

        atexit.register(self.exit_handler)

        self.create_menu_items()
        self.create_widgets()

        self.running = True
        self.root.config(menu=self.menubar)

        self.root.mainloop()

    def exit_handler(self):
        if self.qemu_kill_on_exit.get():
            self.qemu_process.kill()

    def kill_vm(self):
        # Show an error message if the VM is not running
        try:
            if not self.qemu_process.poll() is None:
                alert(
                    title="VM is not running", message="The VM is not running",
                )
                return 1
        except:
            alert(
                title="VM is not running", message="The VM is not running",
            )
            return 1

        # Do you really want to terminate the VM?
        if (
                confirm(
                    "Terminate QEMU",
                    "Are you sure you want to terminate the QEMU process? Any unsaved changes inside the virtual machine will be lost!",
                    icon="warning",
                )
                == "yes"
        ):
            # TODO: Make this work lol
            self.qemu_process.kill()

    def start_vm(self):
        try:
            # Check if QEMU is installed
            if not os.path.exists(f".\\qemu\\{self.qemu_type_box.get()}.exe"):
                alert(
                    "Unable to start the VM",
                    "It seems like QEMU is not installed on your system. Please install it and try again.",
                    icon="error",
                )
                return 1

            # Check if the CD-ROM file exists
            if (not os.path.exists(self.cdrom_path.get())) and (not self.qemu_finish_inst.get()):
                alert(
                    "Unable to start the VM",
                    "The specified CD-ROM file does not exist",
                    icon="error",
                )
                return 1

            # Open QEMU in the background using subprocess.Popen()
            qemu_usb_config = "-usb -device usb-tablet,bus=usb-bus.0 " \
                              "-device usb-mouse,bus=usb-bus.0 " \
                              "-device usb-kbd,bus=usb-bus.0 " \
                              "-device ich9-usb-ehci1,id=usb-controller-0 " \
                              "-device ich9-usb-uhci1,masterbus=usb-controller-0.0,firstport=0,multifunction=on " \
                              "-device ich9-usb-uhci2,masterbus=usb-controller-0.0,firstport=2,multifunction=on " \
                              "-device ich9-usb-uhci3,masterbus=usb-controller-0.0,firstport=4,multifunction=on " \
                              "-chardev spicevmc,name=usbredir,id=usbredirchardev0 " \
                              "-device usb-redir,chardev=usbredirchardev0,id=usbredirdev0,bus=usb-controller-0.0 " \
                              "-chardev spicevmc,name=usbredir,id=usbredirchardev1 " \
                              "-device usb-redir,chardev=usbredirchardev1,id=usbredirdev1,bus=usb-controller-0.0 " \
                              "-chardev spicevmc,name=usbredir,id=usbredirchardev2 " \
                              "-device usb-redir,chardev=usbredirchardev2,id=usbredirdev2,bus=usb-controller-0.0 " \
                              "-device e1000,mac=EA:04:6D:F8:B2:BD,netdev=net0 -netdev user,id=net0 "

            cdrom_config = f"-device ide-cd,bus=ide.0,drive=cdrom0,bootindex=0 " \
                           f"-drive if=none,media=cdrom,id=cdrom0,file={self.cdrom_path.get()} "

            qemu_base_config=f".\\qemu\\{self.qemu_type_box.get()} " \
                             f"-qmp tcp:127.0.0.1:4444,server,nowait " \
                             f"-smp cpus={self.cpu_path.get()},sockets=1,cores={self.cpu_path.get()},threads=1 " \
                             f"-m {self.memory_large.get()} " \
                             f"-device ide-hd,bus=ide.1,drive=drive0,bootindex=1 " \
                             f"-drive if=none,media=disk,id=drive0,file={self.hdd_path.get()},discard=unmap,detect-zeroes=unmap " \
                             f"{qemu_usb_config}" \
                             f"{'' if self.qemu_finish_inst.get() else cdrom_config} " \
                             f"{'-sdl' if self.qemu_sdl_window.get() else ''} " \
                             f"{'-accel hax -accel tcg,thread=multi,tb-size=1024 ' if self.qemu_use_haxm.get() else '-accel tcg,thread=multi,tb-size=1024 '}" \
                             f"-nodefaults -vga none " \
                             f"-device virtio-vga " \
                             f"-machine q35,vmport=off,i8042=off " \
                             f"-device intel-hda " \
                             f"-device hda-duplex " \
                             f"-name VirtualMachine " \
                             f"-boot menu=on" \

            self.qemu_process = Popen(
                qemu_base_config,
                stdout=PIPE,
                stderr=PIPE,
            )

        except CalledProcessError as e:
            # TODO: Improve error messages
            alert(
                title="QEMU Returned an error",
                message=f"QEMU Returned an error: {str(e.output)}",
            )

    def get_first_file_with_ext(self, path, ext):
        # Loop through the specified directory and
        # find a file that has the specified extension
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(ext):
                    return file

        # Return an empty string if no file with the
        # specified extension was found
        return ""

    def not_implemented(self):
        alert("Not Implemented", "This feature has not been implemented yet :P")


    def create_qcow2(self):
        tink=tk.Tk()
        tink.title('Create image')
        tink.geometry('450x300')

        now_nub1 = tk.Label(tink, text='Create disk size (GB)')
        now_nub1.grid(row=1, column=1, sticky='E')
        now_bok1 = tk.Spinbox(tink, values=[i for i in range(1, 999999)], width=5)
        now_bok1.grid(row=1, column=2, sticky='NW')

        Output_results = tk.Label(tink, text='Result:')
        Output_results.grid(row=8, column=1, sticky='NW')
        result_data_Text = tk.Text(tink, width=40, height=2)
        result_data_Text.grid(row=10, column=2, rowspan=15, columnspan=10)

        def value():
            now_lis = [now_bok1.get()]
            now_lis.sort()
            try:
                diskfilecmd = f".\\qemu\\qemu-img create -f qcow2 system.qcow2 %sg" % (now_lis[0])
                self.create_image_process = Popen(
                    diskfilecmd,
                    stdout=PIPE,
                    stderr=PIPE,
                )
            except:
                alert("error")

            result_data_Text = tk.Label(tink, text='successful create %s GB disk file' % (now_lis[0]))
            result_data_Text.grid(row=10, column=2, rowspan=15, columnspan=10)

        AnNiu = tk.Button(tink, text='OK', fg='blue', bd=2, width=10, command=value)
        AnNiu.grid(row=5, column=2, sticky='NW')

        tk.mainloop()

    def create_menu_items(self):
        # Create the menu bar
        self.menubar = tk.Menu(self.root)

        # Adding File Menu and commands
        file = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file)
        file.add_command(label="Preferences...", command=self.not_implemented)
        file.add_separator()
        file.add_command(label="Exit", command=self.root.destroy)

        virtual_machine = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Machine", menu=virtual_machine)
        virtual_machine.add_command(label="Start", command=self.start_vm)
        virtual_machine.add_command(label="Terminate", command=self.kill_vm)

        tools = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools)
        tools.add_command(label="Create HDD Image", command=self.create_qcow2)

        about = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=about)
        about.add_command(
            label="About",
            command=lambda: alert(
                "About",
                "QEMU Manager is a simple GUI frontend for QEMU written in TKinter and Python.\n\nCreated by chainsx",
            ),
        )

    def create_widgets(self):
        # Which formatter should I use to make this look better?
        title_label = ttk.Label(
            self.root,
            text="QEMU Manager",
            anchor="w",
            background=self.root.cget("background"),
            font=("Tahoma", 30),
        )
        title_label.pack(fill="both", padx=18, pady=18)

        # Add a button to start the VM
        self.start_vm_btn = ttk.Button(
            self.root, text="Start VM", command=self.start_vm
        )
        self.start_vm_btn.pack(ipadx=10, ipady=10, padx=10, pady=10)
        self.start_vm_btn.place(x=490, y=510)

        # Add a button to kill the VM
        self.kill_vm_btn = ttk.Button(
            self.root, text="Terminate QEMU", command=self.kill_vm
        )
        self.kill_vm_btn.pack(ipadx=10, ipady=10, padx=10, pady=10)
        self.kill_vm_btn.place(x=360, y=510)

        qemu_type_box_label = ttk.Label(
            self.root, text="CPU Architecture(Require):", background=self.root.cget("background")
        )
        qemu_type_box_label.pack(fill="x", padx=15)

        self.qemu_type_box_value = tk.StringVar()
        self.qemu_type_box_value.set("qemu-system-i386")

        self.qemu_type_box = ttk.Combobox(
            self.root, state="readonly", textvariable=self.qemu_type_box_value
        )
        self.qemu_type_box["values"] = (
            "qemu-system-i386",
            "qemu-system-x86_64",
        )
        self.qemu_type_box.current(1)
        self.qemu_type_box.pack(fill=tk.X, padx=15, pady=5)

        cdrom_path_label = ttk.Label(
            self.root,
            text="CD-ROM (ISO) File Path:",
            background=self.root.cget("background"),
        )
        cdrom_path_label.pack(fill="x", padx=15, pady=5)

        self.cdrom_path_text = tk.StringVar()
        self.cdrom_path_text.set(self.get_first_file_with_ext(os.getcwd(), ".iso"))

        self.cdrom_path = ttk.Entry(self.root, textvariable=self.cdrom_path_text)
        self.cdrom_path.pack(fill="x", padx=15)
        self.cdrom_path.focus()

        hdd_path_label = ttk.Label(
            self.root,
            text="HDD (QCOW2) File Path(Require):",
            background=self.root.cget("background"),
        )
        hdd_path_label.pack(fill="x", padx=15, pady=5)

        self.hdd_path_text = tk.StringVar()
        self.hdd_path_text.set(self.get_first_file_with_ext(os.getcwd(), ".qcow2"))

        self.hdd_path_frame = tk.Frame(
            self.root, bg=self.root.cget("background"), width=450, height=50
        )
        self.hdd_path_frame.grid_columnconfigure(0, weight=1)

        self.hdd_path = ttk.Entry(self.hdd_path_frame, textvariable=self.hdd_path_text)
        self.hdd_path.grid(padx=(15, 0), row=0, column=0, columnspan=1, sticky="we")
        self.hdd_path.focus()

        self.create_hdd_btn = ttk.Button(
            self.hdd_path_frame, text="Create HDD", command=self.create_qcow2
        )
        self.create_hdd_btn.grid(row=0, column=1, padx=(5, 15))

        self.hdd_path_frame.pack(fill="x")

        memory_large_label = ttk.Label(
            self.root,
            text="Memory(MB,Require):",
            background=self.root.cget("background"),
        )
        memory_large_label.pack(fill="x", padx=15, pady=5)

        self.memory_text = tk.StringVar()
        self.memory_text.set("4096")

        self.memory_large = ttk.Entry(self.root, textvariable=self.memory_text)
        self.memory_large.pack(fill="x", padx=15)
        self.memory_large.focus()

        cpu_path_label = ttk.Label(
            self.root,
            text="CPU(s,Require):",
            background=self.root.cget("background"),
        )
        cpu_path_label.pack(fill="x", padx=15, pady=5)

        self.cpu_path_text = tk.StringVar()
        self.cpu_path_text.set("4")

        self.cpu_path_frame = tk.Frame(
            self.root, bg=self.root.cget("background"), width=450, height=50
        )
        self.cpu_path_frame.grid_columnconfigure(0, weight=1)

        self.cpu_path = ttk.Entry(self.root, textvariable=self.cpu_path_text)
        self.cpu_path.pack(fill="x", padx=15)
        self.cpu_path.focus()

        qemu_finish_inst = ttk.Checkbutton(
            self.root ,
            text="Already installed system?" ,
            variable=self.qemu_finish_inst ,
            offvalue=False ,
            onvalue=True ,
            )
        qemu_finish_inst.pack(fill="x" , padx=15 , pady=(10 , 2))

        qemu_sdl_window = ttk.Checkbutton(
            self.root,
            text="Use SDL as the window library?",
            variable=self.qemu_sdl_window,
            offvalue=False,
            onvalue=True,
        )
        qemu_sdl_window.pack(fill="x", padx=15, pady=(10, 2))

        qemu_use_haxm = ttk.Checkbutton(
            self.root,
            text="Use Intel HAXM? (Requires you to have HAXM installed)",
            variable=self.qemu_use_haxm,
            offvalue=False,
            onvalue=True,
        )
        qemu_use_haxm.pack(fill="x", padx=15, pady=2)

        qemu_kill_on_exit_box = ttk.Checkbutton(
            self.root,
            text="Terminate QEMU on Exit?",
            variable=self.qemu_kill_on_exit,
            offvalue=False,
            onvalue=True,
        )
        qemu_kill_on_exit_box.pack(fill="x", padx=15, pady=2)


# Start the manager by constructing a new class
manager = Manager()
