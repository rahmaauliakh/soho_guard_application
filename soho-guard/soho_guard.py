# ==================================================
# IMPORT LIBRARY YANG DIBUTUHKAN
# ==================================================
import tkinter as tk                    # Library utama untuk membuat GUI desktop
from tkinter import messagebox, ttk     # messagebox untuk popup, ttk untuk widget modern
import ipaddress                        # Library untuk manipulasi alamat IP dan subnet
from datetime import datetime           # Untuk mendapatkan timestamp (waktu saat ini)
from reportlab.lib.pagesizes import A4  # Ukuran halaman PDF (A4)
from reportlab.pdfgen import canvas     # Untuk membuat file PDF
import os                               # Untuk operasi file dan folder

# ==================================================
# GLOBAL STATE (Variabel Global)
# ==================================================
# Variabel untuk menyimpan subnet yang sudah digenerate
internal_subnet = None   # Menyimpan subnet untuk jaringan internal (karyawan/server)
guest_subnet = None      # Menyimpan subnet untuk jaringan tamu (guest WiFi)
current_theme = "dark"   # Tema warna aplikasi (dark/light mode)

# ==================================================
# MODERN COLOR PALETTE
# ==================================================
COLORS = {
    "primary": "#6C63FF",       # Purple
    "primary_dark": "#5A52D5",  # Darker Purple
    "secondary": "#00D9FF",     # Cyan
    "accent": "#FF6B9D",        # Pink
    "success": "#00E676",       # Green
    "warning": "#FFB74D",       # Orange
    "danger": "#FF5252",        # Red
    "dark_bg": "#0A0E27",       # Deep Navy
    "dark_card": "#151B3B",     # Card Background
    "dark_surface": "#1E2547",  # Surface
    "dark_border": "#2A3158",   # Border
    "light_bg": "#F0F4FF",      # Light Background
    "light_card": "#FFFFFF",    # White Card
    "light_surface": "#E8EEFF", # Light Surface
    "light_border": "#C8D4FF",  # Light Border
    "text_light": "#FFFFFF",
    "text_dark": "#1A1D3D",
    "text_muted": "#8892B0",
}

THEMES = {
    "dark": {
        "bg": COLORS["dark_bg"],
        "card": COLORS["dark_card"],
        "surface": COLORS["dark_surface"],
        "border": COLORS["dark_border"],
        "fg": COLORS["text_light"],
        "muted": COLORS["text_muted"],
    },
    "light": {
        "bg": COLORS["light_bg"],
        "card": COLORS["light_card"],
        "surface": COLORS["light_surface"],
        "border": COLORS["light_border"],
        "fg": COLORS["text_dark"],
        "muted": "#6B7394",
    }
}

# ==================================================
# INITIAL FILE SETUP (Pengaturan File Awal)
# ==================================================
LOG_FILE = "logs.txt"                                    # Nama file untuk menyimpan log traffic
REPORT_DIR = "reports"                                   # Folder untuk menyimpan laporan PDF
REPORT_FILE = os.path.join(REPORT_DIR, "soho_guard_report.pdf")  # Path lengkap file PDF

# Membuat file log jika belum ada
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, "w").close()  # Buat file kosong

# Membuat folder reports jika belum ada
if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)

# ==================================================
# THEME HANDLER
# ==================================================
def apply_theme():
    theme = THEMES[current_theme]
    root.configure(bg=theme["bg"])
    main_container.configure(bg=theme["bg"])
    canvas_widget.configure(bg=theme["bg"])
    scrollable_frame.configure(bg=theme["bg"])
    
    # Update all widgets recursively
    for widget in scrollable_frame.winfo_children():
        update_widget_theme(widget, theme)

    # Update Combobox Style
    style = ttk.Style()
    style.theme_use('default')
    style.map('TCombobox',
              fieldbackground=[('readonly', theme["surface"])],
              selectbackground=[('readonly', theme["surface"])],
              selectforeground=[('readonly', theme["fg"])],
              background=[('readonly', theme["surface"])],
              foreground=[('readonly', theme["fg"])],
              arrowcolor=[('readonly', theme["fg"])]) # Attempt to color arrow if supported

def update_widget_theme(widget, theme):
    widget_class = widget.winfo_class()
    
    try:
        if widget_class == "Frame":
            if hasattr(widget, 'is_card') and widget.is_card:
                widget.configure(bg=theme["card"])
            else:
                widget.configure(bg=theme["bg"])
        elif widget_class == "Label":
            parent_bg = widget.master.cget('bg') if widget.master else theme["bg"]
            # Keep special colored labels
            current_fg = widget.cget('fg')
            if current_fg not in [COLORS["success"], COLORS["warning"], COLORS["danger"], 
                                  COLORS["primary"], COLORS["secondary"], COLORS["accent"]]:
                if hasattr(widget, 'is_muted') and widget.is_muted:
                    widget.configure(bg=parent_bg, fg=theme["muted"])
                else:
                    widget.configure(bg=parent_bg, fg=theme["fg"])
            else:
                widget.configure(bg=parent_bg)
        elif widget_class == "Entry":
            widget.configure(
                bg=theme["surface"],
                fg=theme["fg"],
                insertbackground=theme["fg"],
                relief="flat",
                highlightthickness=2,
                highlightbackground=theme["border"],
                highlightcolor=COLORS["primary"]
            )
        elif widget_class == "Button":
            widget.configure(
                bg=theme["surface"],
                fg=theme["fg"],
                activebackground=COLORS["primary"],
                activeforeground="white"
            )
    except tk.TclError:
        pass
    
    # Recursively update children
    for child in widget.winfo_children():
        update_widget_theme(child, theme)

def toggle_theme():
    global current_theme
    current_theme = "dark" if current_theme == "light" else "light"
    apply_theme()
    # Update theme button text
    theme_btn.config(text="☀️ Light Mode" if current_theme == "dark" else "🌙 Dark Mode")

# ==================================================
# RESPONSIVE HELPER FUNCTIONS
# ==================================================
def on_frame_configure(event=None):
    canvas_widget.configure(scrollregion=canvas_widget.bbox("all"))

def on_canvas_configure(event):
    canvas_widget.itemconfig(canvas_window, width=event.width)

def on_mousewheel(event):
    canvas_widget.yview_scroll(int(-1*(event.delta/120)), "units")

# ==================================================
# CUSTOM STYLED BUTTON
# ==================================================
class GradientButton(tk.Canvas):
    def __init__(self, parent, text, command, colors=None, width=200, height=45):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, cursor="hand2")
        
        self.command = command
        self.text = text
        self.btn_width = width
        self.btn_height = height
        self.colors = colors or [COLORS["primary"], COLORS["secondary"]]
        
        self.configure(bg=parent.cget('bg'))
        self.draw_button()
        
        self.bind("<Button-1>", lambda e: self.on_click())
        self.bind("<Enter>", lambda e: self.on_hover())
        self.bind("<Leave>", lambda e: self.on_leave())
    
    def draw_button(self, hover=False):
        self.delete("all")
        
        # Draw rounded rectangle with gradient effect
        radius = 12
        if hover:
            self.create_rounded_rect(0, 0, self.btn_width, self.btn_height, radius, 
                                    fill=COLORS["primary_dark"], outline="")
        else:
            self.create_rounded_rect(0, 0, self.btn_width, self.btn_height, radius,
                                    fill=self.colors[0], outline="")
        
        # Add inner rectangle
        self.create_rounded_rect(2, 2, self.btn_width-2, self.btn_height-2, radius-2,
                                fill=self.colors[0] if not hover else COLORS["primary_dark"],
                                outline="")
        
        # Draw text
        self.create_text(self.btn_width/2, self.btn_height/2, text=self.text,
                        fill="white", font=("Segoe UI", 11, "bold"))
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_click(self):
        if self.command:
            self.command()
    
    def on_hover(self):
        self.draw_button(hover=True)
    
    def on_leave(self):
        self.draw_button(hover=False)

# ==================================================
# LOGGING
# ==================================================
def write_log(source, destination, status):
    """
    Fungsi untuk mencatat log traffic ke file logs.txt
    - source: IP sumber traffic
    - destination: IP tujuan traffic
    - status: ALLOWED atau BLOCKED
    """
    # Membuat timestamp dengan format: Tahun-Bulan-Tanggal Jam:Menit:Detik
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Menulis log ke file dengan mode append (menambahkan di akhir file)
    with open(LOG_FILE, "a") as file:
        file.write(f"{timestamp} | SRC={source} -> DST={destination} | {status}\n")

# ==================================================
# SUBNET GENERATOR (Pembuat Subnet)
# ==================================================
def generate_subnet():
    """
    Fungsi UTAMA untuk membagi jaringan menjadi 2 subnet:
    1. Internal Subnet - untuk karyawan/server (lebih trusted)
    2. Guest Subnet - untuk tamu/pengunjung (dibatasi aksesnya)
    
    Konsep: Network Segmentation untuk keamanan SOHO (Small Office Home Office)
    """
    global internal_subnet, guest_subnet
    try:
        # Ambil input IP dan Subnet Mask dari user
        ip_input = entry_ip.get()
        mask_input = combo_mask.get()
        
        # Gabungkan menjadi format CIDR (contoh: 192.168.1.0/24)
        network_input = f"{ip_input}/{mask_input}"
        
        # Konversi string menjadi objek ip_network
        # strict=False: mengizinkan host bits (misal 192.168.1.5/24)
        network = ipaddress.ip_network(network_input, strict=False)

        # SUBNETTING: Membagi network menjadi 2 subnet yang lebih kecil
        # Contoh: /24 dibagi menjadi 2 subnet /25
        # new_prefix = network.prefixlen + 1
        subnets = list(network.subnets(new_prefix=network.prefixlen + 1))
        internal_subnet, guest_subnet = subnets  # Subnet pertama = internal, kedua = guest

        # Mendapatkan daftar host yang bisa dipakai di setiap subnet
        i_hosts = list(internal_subnet.hosts())  # Host internal (tanpa network & broadcast)
        g_hosts = list(guest_subnet.hosts())     # Host guest

        # Update tampilan GUI untuk Internal Subnet
        label_internal_net.config(text=f"{internal_subnet.network_address}")
        label_internal_broadcast.config(text=f"{internal_subnet.broadcast_address}")
        label_internal_range.config(text=f"{i_hosts[0]} - {i_hosts[-1]}")

        # Update tampilan GUI untuk Guest Subnet
        label_guest_net.config(text=f"{guest_subnet.network_address}")
        label_guest_broadcast.config(text=f"{guest_subnet.broadcast_address}")
        label_guest_range.config(text=f"{g_hosts[0]} - {g_hosts[-1]}")

        label_status.config(text="✨ Subnet berhasil dibuat!", fg=COLORS["success"])

    except Exception:
        messagebox.showerror("Error", "Format IP Network tidak valid!")

# ==================================================
# TRAFFIC SIMULATION (Simulasi Lalu Lintas Jaringan)
# ==================================================
def simulate_traffic():
    """
    Fungsi INTI untuk simulasi firewall/traffic filtering
    
    ATURAN KEAMANAN (Firewall Rule):
    - Guest TIDAK BOLEH mengakses Internal (BLOCKED)
    - Internal boleh mengakses Guest (ALLOWED)
    - Internal ke Internal (ALLOWED)
    - Guest ke Guest (ALLOWED)
    
    Ini adalah implementasi sederhana dari Network Access Control (NAC)
    """
    # Validasi: Pastikan subnet sudah dibuat terlebih dahulu
    if internal_subnet is None or guest_subnet is None:
        messagebox.showwarning("Warning", "Subnet belum dibuat!")
        return

    try:
        # Konversi input string menjadi objek IP address
        src_ip = ipaddress.ip_address(entry_source.get())       # IP sumber
        dst_ip = ipaddress.ip_address(entry_destination.get())  # IP tujuan

        # ============================================
        # LOGIKA FIREWALL RULE:
        # Jika source IP ada di Guest subnet DAN 
        # destination IP ada di Internal subnet -> BLOKIR!
        # ============================================
        if src_ip in guest_subnet and dst_ip in internal_subnet:
            # Traffic dari Guest ke Internal = DIBLOKIR (keamanan!)
            label_status.config(text="🚫 BLOCKED - Guest ke Internal", fg=COLORS["danger"])
            write_log(src_ip, dst_ip, "BLOCKED")
        else:
            # Semua traffic lainnya = DIIZINKAN
            label_status.config(text="✅ ALLOWED - Traffic diizinkan", fg=COLORS["success"])
            write_log(src_ip, dst_ip, "ALLOWED")

    except ValueError:
        # Error handling jika format IP tidak valid
        messagebox.showerror("Error", "IP Source atau Destination tidak valid!")

# ==================================================
# PDF REPORT GENERATOR (Pembuat Laporan PDF)
# ==================================================
def generate_pdf_report():
    """
    Fungsi untuk membuat laporan PDF yang berisi:
    - Informasi subnet yang sudah dibuat
    - Log traffic terakhir (12 entri terbaru)
    
    Menggunakan library ReportLab untuk generate PDF
    """
    # Validasi: Pastikan ada data subnet
    if internal_subnet is None:
        messagebox.showwarning("Warning", "Tidak ada data subnet untuk dilaporkan!")
        return

    # Membuat canvas PDF dengan ukuran A4
    c = canvas.Canvas(REPORT_FILE, pagesize=A4)
    width, height = A4  # Mendapatkan dimensi halaman A4

    # Menulis judul laporan (font bold, ukuran 16)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "SOHO Guard - Network Security Report")

    # Menulis informasi subnet (font normal, ukuran 10)
    c.setFont("Helvetica", 10)
    y = height - 100  # Posisi Y untuk mulai menulis

    c.drawString(50, y, f"Internal Subnet : {internal_subnet}")
    y -= 15
    c.drawString(50, y, f"Guest Subnet    : {guest_subnet}")

    # Menulis log traffic
    y -= 30
    c.drawString(50, y, "Traffic Logs:")
    y -= 20

    # Membaca file log dan menampilkan 12 baris terakhir
    with open(LOG_FILE, "r") as file:
        for line in file.readlines()[-12:]:  # Ambil 12 log terakhir
            c.drawString(60, y, line[:95])    # Batasi 95 karakter per baris
            y -= 15  # Geser posisi ke bawah

    # Simpan file PDF
    c.save()
    messagebox.showinfo("Success", "Laporan PDF berhasil dibuat!")

# ==================================================
# GUI SETUP - RESPONSIVE
# ==================================================
root = tk.Tk()
root.title("SOHO Guard - Network Security")
root.geometry("900x780")
root.minsize(360, 600)  # Minimum size updated for mobile
root.configure(bg=COLORS["dark_bg"])

# Configure grid weights for responsiveness
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# ==================================================
# MAIN SCROLLABLE CONTAINER
# ==================================================
main_container = tk.Frame(root, bg=COLORS["dark_bg"])
main_container.grid(row=0, column=0, sticky="nsew")
main_container.grid_rowconfigure(0, weight=1)
main_container.grid_columnconfigure(0, weight=1)

# Canvas for scrolling
canvas_widget = tk.Canvas(main_container, bg=COLORS["dark_bg"], highlightthickness=0)
canvas_widget.grid(row=0, column=0, sticky="nsew")

# Scrollbar
scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas_widget.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
canvas_widget.configure(yscrollcommand=scrollbar.set)

# Scrollable frame inside canvas
scrollable_frame = tk.Frame(canvas_widget, bg=COLORS["dark_bg"])
canvas_window = canvas_widget.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Bind scroll events
scrollable_frame.bind("<Configure>", on_frame_configure)
canvas_widget.bind("<Configure>", on_canvas_configure)
root.bind_all("<MouseWheel>", on_mousewheel)

# ==================================================
# HEADER SECTION
# ==================================================
header_frame = tk.Frame(scrollable_frame, bg=COLORS["dark_bg"])
header_frame.pack(pady=20, fill="x", padx=20)

# Logo/Title
title_label = tk.Label(
    header_frame, 
    text="🛡️ SOHO GUARD",
    font=("Segoe UI", 28, "bold"),
    fg=COLORS["primary"],
    bg=COLORS["dark_bg"]
)
title_label.pack()

# Try to load logo image
try:
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        # Keep reference to prevent GC
        logo_image = tk.PhotoImage(file=logo_path)
        # Set as window icon
        root.iconphoto(False, logo_image)
except Exception as e:
    print(f"Error loading logo: {e}")

subtitle_label = tk.Label(
    header_frame,
    text="Network Segmentation & Security Simulator",
    font=("Segoe UI", 11),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_bg"]
)
subtitle_label.is_muted = True
subtitle_label.pack(pady=(5, 0))

# Theme toggle button
theme_btn = tk.Button(
    header_frame,
    text="☀️ Light Mode",
    command=toggle_theme,
    font=("Segoe UI", 10),
    bg=COLORS["dark_surface"],
    fg=COLORS["text_light"],
    relief="flat",
    padx=15,
    pady=5,
    cursor="hand2",
    activebackground=COLORS["primary"],
    activeforeground="white"
)
theme_btn.pack(pady=10)

# ==================================================
# NETWORK INPUT CARD
# ==================================================
input_card = tk.Frame(scrollable_frame, bg=COLORS["dark_card"], padx=25, pady=20)
input_card.pack(pady=10, padx=20, fill="x")
input_card.is_card = True

input_title = tk.Label(
    input_card,
    text="📡 Network Configuration",
    font=("Segoe UI", 14, "bold"),
    fg=COLORS["secondary"],
    bg=COLORS["dark_card"]
)
input_title.pack(anchor="w")

input_subtitle = tk.Label(
    input_card,
    text="Masukkan IP Address dan Pilih Subnet Mask",
    font=("Segoe UI", 10),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_card"]
)
input_subtitle.is_muted = True
input_subtitle.pack(anchor="w", pady=(10, 5))

input_fields_frame = tk.Frame(input_card, bg=COLORS["dark_card"])
input_fields_frame.pack(anchor="w", fill="x", pady=(0, 5))

# Configure grid weights
input_fields_frame.grid_columnconfigure(0, weight=7)
input_fields_frame.grid_columnconfigure(1, weight=3)

# IP Address Input
ip_frame = tk.Frame(input_fields_frame, bg=COLORS["dark_card"])
ip_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))

tk.Label(
    ip_frame,
    text="IP Address",
    font=("Segoe UI", 10),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_card"]
).pack(anchor="w")

entry_ip = tk.Entry(
    ip_frame,
    font=("Consolas", 12),
    bg=COLORS["dark_surface"],
    fg=COLORS["text_light"],
    insertbackground=COLORS["text_light"],
    relief="flat",
    highlightthickness=2,
    highlightbackground=COLORS["dark_border"],
    highlightcolor=COLORS["primary"]
)
entry_ip.pack(anchor="w", fill="x", ipady=8)

# Subnet Mask Input (Combobox)
mask_frame = tk.Frame(input_fields_frame, bg=COLORS["dark_card"])
mask_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))

tk.Label(
    mask_frame,
    text="Subnet Mask",
    font=("Segoe UI", 10),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_card"]
).pack(anchor="w")

combo_mask = ttk.Combobox(
    mask_frame,
    values=[str(i) for i in range(8, 31)], # CIDR /8 to /30
    font=("Consolas", 12),
    state="readonly",
    width=5
)
combo_mask.set("24") # Default to /24
combo_mask.pack(anchor="w", fill="x", ipady=8)

# Style for Combobox (needs some wrestling with ttk styles)
style = ttk.Style()
style.theme_use('default')
style.map('TCombobox', fieldbackground=[('readonly', COLORS["dark_surface"])],
                      selectbackground=[('readonly', COLORS["dark_surface"])],
                      selectforeground=[('readonly', COLORS["text_light"])],
                      background=[('readonly', COLORS["dark_surface"])],
                      foreground=[('readonly', COLORS["text_light"])])


# Generate Button
generate_btn_frame = tk.Frame(input_card, bg=COLORS["dark_card"])
generate_btn_frame.pack(anchor="w", pady=(15, 0))

generate_btn = GradientButton(
    generate_btn_frame,
    text="⚡ Generate Subnet",
    command=generate_subnet,
    colors=[COLORS["primary"], COLORS["secondary"]],
    width=180,
    height=42
)
generate_btn.pack()

# ==================================================
# SUBNET DISPLAY CARDS - RESPONSIVE GRID
# ==================================================
subnet_container = tk.Frame(scrollable_frame, bg=COLORS["dark_bg"])
subnet_container.pack(pady=15, padx=20, fill="x")

# Configure column weights for responsiveness
subnet_container.grid_columnconfigure(0, weight=1)
subnet_container.grid_columnconfigure(1, weight=1)

# Internal Subnet Card
internal_card = tk.Frame(
    subnet_container,
    bg=COLORS["dark_card"],
    padx=20,
    pady=15
)
internal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)
internal_card.is_card = True

internal_title = tk.Label(
    internal_card,
    text="🏢 INTERNAL SUBNET",
    font=("Segoe UI", 12, "bold"),
    fg=COLORS["success"],
    bg=COLORS["dark_card"]
)
internal_title.pack(anchor="w")

tk.Frame(internal_card, bg=COLORS["dark_border"], height=1).pack(fill="x", pady=10)

# Internal subnet details
for row_data in [("Network", "label_internal_net"), ("Broadcast", "label_internal_broadcast"), ("Host Range", "label_internal_range")]:
    row = tk.Frame(internal_card, bg=COLORS["dark_card"])
    row.pack(fill="x", pady=2)
    lbl_title = tk.Label(row, text=f"{row_data[0]}:", font=("Segoe UI", 9), fg=COLORS["text_muted"], bg=COLORS["dark_card"], width=12, anchor="w")
    lbl_title.is_muted = True
    lbl_title.pack(side="left")
    lbl = tk.Label(row, text="-", font=("Consolas", 10), fg=COLORS["text_light"], bg=COLORS["dark_card"])
    lbl.pack(side="left", fill="x", expand=True)
    globals()[row_data[1]] = lbl

# Guest Subnet Card
guest_card = tk.Frame(
    subnet_container,
    bg=COLORS["dark_card"],
    padx=20,
    pady=15
)
guest_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)
guest_card.is_card = True

guest_title = tk.Label(
    guest_card,
    text="👥 GUEST SUBNET",
    font=("Segoe UI", 12, "bold"),
    fg=COLORS["warning"],
    bg=COLORS["dark_card"]
)
guest_title.pack(anchor="w")

tk.Frame(guest_card, bg=COLORS["dark_border"], height=1).pack(fill="x", pady=10)

# Guest subnet details
for row_data in [("Network", "label_guest_net"), ("Broadcast", "label_guest_broadcast"), ("Host Range", "label_guest_range")]:
    row = tk.Frame(guest_card, bg=COLORS["dark_card"])
    row.pack(fill="x", pady=2)
    lbl_title = tk.Label(row, text=f"{row_data[0]}:", font=("Segoe UI", 9), fg=COLORS["text_muted"], bg=COLORS["dark_card"], width=12, anchor="w")
    lbl_title.is_muted = True
    lbl_title.pack(side="left")
    lbl = tk.Label(row, text="-", font=("Consolas", 10), fg=COLORS["text_light"], bg=COLORS["dark_card"])
    lbl.pack(side="left", fill="x", expand=True)
    globals()[row_data[1]] = lbl

# ==================================================
# TRAFFIC SIMULATION CARD
# ==================================================
traffic_card = tk.Frame(scrollable_frame, bg=COLORS["dark_card"], padx=25, pady=20)
traffic_card.pack(pady=10, padx=20, fill="x")
traffic_card.is_card = True

traffic_title = tk.Label(
    traffic_card,
    text="🔄 Traffic Simulation",
    font=("Segoe UI", 14, "bold"),
    fg=COLORS["accent"],
    bg=COLORS["dark_card"]
)
traffic_title.pack(anchor="w")

# Input fields container - responsive
input_fields = tk.Frame(traffic_card, bg=COLORS["dark_card"])
input_fields.pack(fill="x", pady=(15, 0))

# Configure columns for responsiveness
input_fields.grid_columnconfigure(0, weight=1)
input_fields.grid_columnconfigure(1, weight=1)

# Source IP
src_container = tk.Frame(input_fields, bg=COLORS["dark_card"])
src_container.grid(row=0, column=0, sticky="ew", padx=(0, 10))

src_label = tk.Label(
    src_container,
    text="Source IP",
    font=("Segoe UI", 10),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_card"]
)
src_label.is_muted = True
src_label.pack(anchor="w")

entry_source = tk.Entry(
    src_container,
    font=("Consolas", 11),
    bg=COLORS["dark_surface"],
    fg=COLORS["text_light"],
    insertbackground=COLORS["text_light"],
    relief="flat",
    highlightthickness=2,
    highlightbackground=COLORS["dark_border"],
    highlightcolor=COLORS["primary"]
)
entry_source.pack(anchor="w", ipady=6, fill="x")

# Destination IP
dst_container = tk.Frame(input_fields, bg=COLORS["dark_card"])
dst_container.grid(row=0, column=1, sticky="ew", padx=(10, 0))

dst_label = tk.Label(
    dst_container,
    text="Destination IP",
    font=("Segoe UI", 10),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_card"]
)
dst_label.is_muted = True
dst_label.pack(anchor="w")

entry_destination = tk.Entry(
    dst_container,
    font=("Consolas", 11),
    bg=COLORS["dark_surface"],
    fg=COLORS["text_light"],
    insertbackground=COLORS["text_light"],
    relief="flat",
    highlightthickness=2,
    highlightbackground=COLORS["dark_border"],
    highlightcolor=COLORS["primary"]
)
entry_destination.pack(anchor="w", ipady=6, fill="x")

# Simulate Button
simulate_btn_frame = tk.Frame(traffic_card, bg=COLORS["dark_card"])
simulate_btn_frame.pack(anchor="w", pady=(15, 0))

simulate_btn = GradientButton(
    simulate_btn_frame,
    text="🚀 Simulate Traffic",
    command=simulate_traffic,
    colors=[COLORS["accent"], COLORS["primary"]],
    width=180,
    height=42
)
simulate_btn.pack()

# ==================================================
# BOTTOM SECTION - REPORT & STATUS
# ==================================================
bottom_frame = tk.Frame(scrollable_frame, bg=COLORS["dark_bg"])
bottom_frame.pack(pady=15, padx=20, fill="x")

# PDF Report Button - centered
report_btn_frame = tk.Frame(bottom_frame, bg=COLORS["dark_bg"])
report_btn_frame.pack()

report_btn = GradientButton(
    report_btn_frame,
    text="📄 Generate PDF Report",
    command=generate_pdf_report,
    colors=[COLORS["secondary"], COLORS["success"]],
    width=220,
    height=45
)
report_btn.pack()

# Status Label Card
status_card = tk.Frame(scrollable_frame, bg=COLORS["dark_card"], padx=20, pady=15)
status_card.pack(pady=10, padx=20, fill="x")
status_card.is_card = True

label_status = tk.Label(
    status_card,
    text="⏳ STATUS: Menunggu input...",
    font=("Segoe UI", 13, "bold"),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_card"]
)
label_status.is_muted = True
label_status.pack()

# ==================================================
# FOOTER
# ==================================================
footer_label = tk.Label(
    scrollable_frame,
    text="© 2026 SOHO Guard | Network Security Made Simple",
    font=("Segoe UI", 9),
    fg=COLORS["text_muted"],
    bg=COLORS["dark_bg"]
)
footer_label.is_muted = True
footer_label.pack(pady=(5, 20))

# ==================================================
# RESPONSIVE LAYOUT ADJUSTMENTS
# ==================================================
def adjust_layout(event=None):
    """Adjust layout based on window width"""
    width = root.winfo_width()
    
    if width < 700:
        # Stack subnet cards vertically on small screens
        internal_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=5)
        guest_card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=5)
        
        # Stack traffic simulation inputs vertically
        src_container.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 10))
        dst_container.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
    else:
        # Side by side on larger screens
        internal_card.grid(row=0, column=0, columnspan=1, sticky="nsew", padx=(0, 8), pady=5)
        guest_card.grid(row=0, column=1, columnspan=1, sticky="nsew", padx=(8, 0), pady=5)
        
        src_container.grid(row=0, column=0, columnspan=1, sticky="ew", padx=(0, 10))
        dst_container.grid(row=0, column=1, columnspan=1, sticky="ew", padx=(10, 0))

    if width < 450:
         # Stack network input fields vertically very small screens
        ip_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 10))
        mask_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
    else:
        # Side by side for network inputs
        ip_frame.grid(row=0, column=0, columnspan=1, sticky="ew", padx=(0, 10), pady=0)
        mask_frame.grid(row=0, column=1, columnspan=1, sticky="ew", padx=(10, 0), pady=0)

# Bind resize event
root.bind("<Configure>", adjust_layout)

apply_theme()
root.mainloop()
