import os
import sys
import subprocess
import threading
import socket
import re
import customtkinter as ctk
from tkinter import messagebox
import psutil

class GoDispatchProxyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configurazione della finestra principale
        self.title("Go Dispatch Proxy GUI")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Imposta il tema scuro come predefinito
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Variabili di stato
        self.proxy_process = None
        self.running = False
        self.selected_ips = []
        
        # Crea il layout principale
        self.create_layout()
        
        # Carica gli indirizzi IP disponibili
        self.load_ip_addresses()
        
        # Protocolla la chiusura della finestra
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_layout(self):
        # Frame principale con due colonne
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)
        
        # Frame sinistro per le opzioni e selezione IP
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Frame destro per l'output
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.create_left_panel()
        self.create_right_panel()
    
    def create_left_panel(self):
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        # Titolo
        title_label = ctk.CTkLabel(
            self.left_frame, 
            text="Go Dispatch Proxy", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=(20, 10), sticky="w")
        
        # Sottotitolo
        subtitle_label = ctk.CTkLabel(
            self.left_frame, 
            text="Select interfaces and configure options", 
            font=ctk.CTkFont(size=12)
        )
        subtitle_label.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="w")
        
        # Frame per le opzioni
        options_frame = ctk.CTkFrame(self.left_frame)
        options_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)
        
        # LHOST
        ctk.CTkLabel(options_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.lhost_var = ctk.StringVar(value="127.0.0.1")
        lhost_entry = ctk.CTkEntry(options_frame, textvariable=self.lhost_var)
        lhost_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # LPORT
        ctk.CTkLabel(options_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.lport_var = ctk.StringVar(value="8080")
        lport_entry = ctk.CTkEntry(options_frame, textvariable=self.lport_var)
        lport_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Opzioni tunnel e quiet
        self.tunnel_var = ctk.BooleanVar(value=False)
        tunnel_switch = ctk.CTkSwitch(options_frame, text="Tunnel Mode", variable=self.tunnel_var)
        tunnel_switch.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.quiet_var = ctk.BooleanVar(value=False)
        quiet_switch = ctk.CTkSwitch(options_frame, text="Quiet Mode", variable=self.quiet_var)
        quiet_switch.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Lista di interfacce
        interfaces_label = ctk.CTkLabel(self.left_frame, text="Available physical interfaces:", anchor="w")
        interfaces_label.grid(row=3, column=0, padx=10, pady=(20, 5), sticky="w")
        
        # Frame con scrollbar per la lista IP
        ip_frame = ctk.CTkFrame(self.left_frame)
        ip_frame.grid(row=4, column=0, padx=10, pady=5, sticky="nsew")
        self.left_frame.grid_rowconfigure(4, weight=1)
        
        ip_frame.grid_rowconfigure(0, weight=1)
        ip_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable frame per IP
        self.ip_scrollable_frame = ctk.CTkScrollableFrame(ip_frame)
        self.ip_scrollable_frame.grid(row=0, column=0, sticky="nsew")
        self.ip_scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Il contenuto delle checkbox IP sarà popolato dalla funzione load_ip_addresses
        self.ip_vars = []
        self.ip_checkboxes = []
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            self.left_frame, 
            text="Refresh interfaces", 
            command=self.load_ip_addresses,
            fg_color="#2B7A0B",
            hover_color="#3A9614"
        )
        refresh_button.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        
        # Start/Stop button
        self.start_button = ctk.CTkButton(
            self.left_frame, 
            text="Start Proxy", 
            command=self.toggle_proxy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.grid(row=6, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        # Theme selector
        theme_frame = ctk.CTkFrame(self.left_frame)
        theme_frame.grid(row=7, column=0, padx=10, pady=(0, 10), sticky="ew")
        theme_frame.grid_columnconfigure(0, weight=1)
        theme_frame.grid_columnconfigure(1, weight=1)
        
        theme_label = ctk.CTkLabel(theme_frame, text="Theme:")
        theme_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        theme_options = ["dark", "light", "system"]
        theme_dropdown = ctk.CTkOptionMenu(
            theme_frame, 
            values=theme_options,
            command=self.change_theme
        )
        theme_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        theme_dropdown.set("dark")
    
    def create_right_panel(self):
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=0)
        self.right_frame.grid_rowconfigure(1, weight=1)
        
        # Titolo del pannello
        output_title = ctk.CTkLabel(
            self.right_frame, 
            text="Proxy output", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        output_title.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Textbox per l'output
        self.output_textbox = ctk.CTkTextbox(self.right_frame, wrap="word")
        self.output_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.output_textbox.configure(state="disabled")
    
    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)
    
    def load_ip_addresses(self):
        # Pulisce le checkboxes esistenti
        for checkbox in self.ip_checkboxes:
            checkbox.destroy()
        
        self.ip_vars = []
        self.ip_checkboxes = []
        
        try:
            # Ottiene gli indirizzi IP locali con nome dell'interfaccia
            interfaces = self.get_network_interfaces()
            
            # Crea una checkbox per ogni indirizzo IP
            for i, (ip, interface_name) in enumerate(interfaces):
                var = ctk.BooleanVar(value=False)
                self.ip_vars.append((var, ip))
                
                checkbox = ctk.CTkCheckBox(
                    self.ip_scrollable_frame, 
                    text=f"{ip} ({interface_name})",
                    variable=var,
                    onvalue=True,
                    offvalue=False
                )
                checkbox.grid(row=i, column=0, padx=10, pady=5, sticky="w")
                self.ip_checkboxes.append(checkbox)
            
            # Se non ci sono interfacce
            if not interfaces:
                label = ctk.CTkLabel(self.ip_scrollable_frame, text="No physical interfaces available")
                label.grid(row=0, column=0, padx=10, pady=10)
                self.ip_checkboxes.append(label)
        
        except Exception as e:
            self.update_output(f"Error loading interfaces: {str(e)}")
            label = ctk.CTkLabel(self.ip_scrollable_frame, text="Error loading interfaces")
            label.grid(row=0, column=0, padx=10, pady=10)
            self.ip_checkboxes.append(label)
    
    def get_network_interfaces(self):
        """Ottiene solo le interfacce di rete fisiche attive con i loro indirizzi IP"""
        interfaces = []
        
        try:
            # Otteniamo informazioni sulle interfacce di rete
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            # Filtriamo solo le interfacce fisiche attive
            for interface, addrs in net_if_addrs.items():
                # Verifichiamo se l'interfaccia è attiva
                if interface in net_if_stats and net_if_stats[interface].isup:
                    # Escludiamo interfacce virtuali comuni
                    if not self.is_virtual_interface(interface):
                        for addr in addrs:
                            # Consideriamo solo gli indirizzi IPv4
                            if addr.family == socket.AF_INET:
                                # Escludiamo gli indirizzi loopback e link-local
                                ip = addr.address
                                if not (ip.startswith('127.') or ip.startswith('169.254.')):
                                    interfaces.append((ip, interface))
            
            # Se non troviamo interfacce, proviamo il comando -list del proxy
            if not interfaces:
                try:
                    result = subprocess.run(["go-dispatch-proxy.exe", "-list"], 
                                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    # Analizza l'output per estrarre gli indirizzi IP
                    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
                    ips = re.findall(ip_pattern, result.stdout)
                    
                    for ip in ips:
                        # Escludiamo gli indirizzi loopback e link-local
                        if not (ip.startswith('127.') or ip.startswith('169.254.')):
                            interfaces.append((ip, "Interface detected by go-dispatch-proxy"))
                except:
                    pass
        
        except Exception as e:
            self.update_output(f"Error loading interfaces: {str(e)}")
        
        return interfaces
        
    def is_virtual_interface(self, interface_name):
        """Determina se un'interfaccia è probabilmente virtuale"""
        # Lista di pattern comuni per interfacce virtuali
        virtual_patterns = [
            'vmware', 'virtual', 'vethernet', 'veth', 'docker', 'lo', 'loopback', 
            'tap', 'tun', 'vpn', 'bridge', 'vbox', 'hyper-v', 'pseudo', 'vnic',
            'miniport', 'wsl', 'nordlynx', 'mullvad'
        ]
        
        name_lower = interface_name.lower()
        
        # Controlla se il nome dell'interfaccia contiene uno dei pattern virtuali
        for pattern in virtual_patterns:
            if pattern in name_lower:
                return True
        
        return False
    
    def toggle_proxy(self):
        if not self.running:
            self.start_proxy()
        else:
            self.stop_proxy()
    
    def start_proxy(self):
        # Ottieni gli IP selezionati
        selected_ips = [ip for var, ip in self.ip_vars if var.get()]
        
        if not selected_ips:
            messagebox.showerror("Error", "Select at least one IP address!")
            return
        
        # Preparare il comando
        command = ["go-dispatch-proxy.exe"]
        
        # Aggiungi le opzioni
        if self.lhost_var.get():
            command.extend(["-lhost", self.lhost_var.get()])
        
        if self.lport_var.get():
            command.extend(["-lport", self.lport_var.get()])
        
        if self.tunnel_var.get():
            command.append("-tunnel")
        
        if self.quiet_var.get():
            command.append("-quiet")
        
        # Aggiungi gli IP selezionati
        command.extend(selected_ips)
        
        try:
            # Aggiorna l'interfaccia per mostrare che stiamo avviando il proxy
            self.update_output("Starting proxy...\n")
            self.update_output(f"Command: {' '.join(command)}\n\n")
            
            # Avvia il processo nascosto
            self.proxy_process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Aggiorna lo stato
            self.running = True
            self.start_button.configure(text="Stop Proxy", fg_color="#C41E3A", hover_color="#E32636")
            
            # Avvia un thread per leggere l'output
            threading.Thread(target=self.read_output, daemon=True).start()
            
        except Exception as e:
            self.update_output(f"Unable to start proxy: {str(e)}")
            messagebox.showerror("Error", f"Unable to start proxy: {str(e)}")
    
    def stop_proxy(self):
        if self.proxy_process:
            try:
                # Termina il processo
                if self.proxy_process.poll() is None:  # Se il processo è ancora in esecuzione
                    self.proxy_process.terminate()
                    try:
                        self.proxy_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.proxy_process.kill()
                
                self.update_output("\nProxy stopped.\n")
                
            except Exception as e:
                self.update_output(f"\nError stopping proxy: {str(e)}")
            
            finally:
                # Resetta lo stato
                self.running = False
                self.proxy_process = None
                self.start_button.configure(text="Avvia Proxy", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"])
    
    def read_output(self):
        """Legge l'output dal processo del proxy e lo aggiorna nell'interfaccia"""
        if not self.proxy_process:
            return
        
        while self.proxy_process.poll() is None:  # Finché il processo è in esecuzione
            line = self.proxy_process.stdout.readline()
            if line:
                self.update_output(line)
        
        # Leggi eventuali output rimanenti
        remaining_output = self.proxy_process.stdout.read()
        if remaining_output:
            self.update_output(remaining_output)
        
        # Se il processo è terminato da solo
        if self.running:
            self.running = False
            self.proxy_process = None
            
            # Aggiorna il pulsante nell'interfaccia utente (thread-safe)
            self.after(0, lambda: self.start_button.configure(
                text="Start Proxy", 
                fg_color=["#3B8ED0", "#1F6AA5"], 
                hover_color=["#36719F", "#144870"]
            ))
            
            self.update_output("\nThe proxy has unexpectedly stopped.\n")
    
    def update_output(self, text):
        """Aggiorna la casella di testo dell'output in modo thread-safe"""
        def _update():
            self.output_textbox.configure(state="normal")
            self.output_textbox.insert("end", text)
            self.output_textbox.see("end")
            self.output_textbox.configure(state="disabled")
        
        # Assicura che l'aggiornamento dell'interfaccia avvenga nel thread principale
        self.after(0, _update)
    
    def on_closing(self):
        """Gestisce la chiusura dell'applicazione"""
        if self.running:
            self.stop_proxy()
        
        self.destroy()

if __name__ == "__main__":
    app = GoDispatchProxyGUI()
    app.mainloop()
