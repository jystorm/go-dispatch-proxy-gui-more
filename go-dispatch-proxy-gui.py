import os
import sys
import subprocess
import threading
import socket
import re
import customtkinter as ctk
from tkinter import messagebox
import psutil
import time

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
        
        # NIC 통계 초기화 및 업데이트 루프 시작
        self.nic_prev_counters = {}
        self.last_stats_time = time.time()
        self.nic_stat_labels = {}
        self.update_nic_stats()
        
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
        # NIC 목록 프레임 (초기 높이는 작게, 이후 동적으로 조정)
        self.ip_frame = ctk.CTkFrame(self.left_frame, height=1)
        self.ip_frame.grid(row=4, column=0, padx=5, pady=(0,2), sticky="ew")
        self.left_frame.grid_rowconfigure(4, weight=0)  # 자동 세로 확장 끄기
        self.ip_frame.grid_propagate(False)  # 내부 위젯에 따라 자동 크기 조정 막기

        self.ip_frame.grid_rowconfigure(0, weight=1)
        self.ip_frame.grid_columnconfigure(0, weight=1)

        # 스크롤 영역 (height 나중에 설정)
        self.ip_scrollable_frame = ctk.CTkScrollableFrame(self.ip_frame)
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
        refresh_button.grid(row=5, column=0, padx=10, pady=(5,4), sticky="ew")
        
        # Start/Stop button
        self.start_button = ctk.CTkButton(
            self.left_frame, 
            text="Start Proxy", 
            command=self.toggle_proxy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.grid(row=6, column=0, padx=10, pady=(4, 10), sticky="ew")
        
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
        self.right_frame.grid_rowconfigure(1, weight=5)
        self.right_frame.grid_rowconfigure(2, weight=0)
        
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
        
        # --- NIC statistics panel ---
        self.stats_frame = ctk.CTkFrame(self.right_frame)
        self.stats_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.stats_frame.grid_columnconfigure(0, weight=1)

        stats_title = ctk.CTkLabel(
            self.stats_frame,
            text="NIC statistics",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_title.grid(row=0, column=0, sticky="w")

        # Frame to contain dynamic NIC labels
        self.stats_content = ctk.CTkFrame(self.stats_frame)
        self.stats_content.grid(row=1, column=0, sticky="ew")
        self.stats_content.grid_columnconfigure(0, weight=1)
    
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
            # Store physical NIC names for stats filtering
            self.physical_nics = [name for _, name in interfaces]
            
            # Crea una checkbox + Spinbox per ogni indirizzo IP
            for i, (ip, interface_name) in enumerate(interfaces):
                var = ctk.BooleanVar(value=False)
                weight_var = ctk.IntVar(value=1)
                self.ip_vars.append((var, ip, weight_var))

                # Frame per checkbox + slider
                row_frame = ctk.CTkFrame(self.ip_scrollable_frame)
                row_frame.grid(row=i, column=0, padx=0, pady=0, sticky="ew")  # 여백 최소화
                row_frame.grid_columnconfigure(1, weight=1)
                row_frame.grid_columnconfigure(2, weight=0)

                checkbox = ctk.CTkCheckBox(
                    row_frame, 
                    text=f"{ip} ({interface_name})",
                    variable=var,
                    onvalue=True,
                    offvalue=False
                )
                checkbox.grid(row=0, column=0, sticky="w")

                # 슬라이더(가중치)
                def slider_callback(value, weight_var=weight_var, value_label=None):
                    int_val = int(round(value))
                    weight_var.set(int_val)
                    if value_label is not None:
                        value_label.configure(text=str(int_val))
                weight_slider = ctk.CTkSlider(row_frame, from_=1, to=4, number_of_steps=3, orientation="horizontal")
                weight_slider.set(1)
                weight_slider.configure(width=120)
                weight_slider.grid(row=0, column=1, padx=(10,0), sticky="e")

                # 값 표시 Label
                value_label = ctk.CTkLabel(row_frame, text="1", width=20)
                value_label.grid(row=0, column=2, padx=(8,0), sticky="e")

                # 슬라이더 값 변경 시 label 동기화
                weight_slider.configure(command=lambda value, wv=weight_var, vl=value_label: slider_callback(value, wv, vl))

                self.ip_checkboxes.append(row_frame)
            
            # Se non ci sono interfacce
            if not interfaces:
                label = ctk.CTkLabel(self.ip_scrollable_frame, text="No physical interfaces available")
                label.grid(row=0, column=0, padx=10, pady=10)
                self.ip_checkboxes.append(label)

            # --- After populating, adjust frame height dynamically ---
            count = len(interfaces)
            visible = min(count, 4)
            row_height = 38  # approximate row height
            target_height = max(visible * row_height, 80)  # 최소 80
            self.ip_scrollable_frame.configure(height=target_height)
            self.ip_frame.configure(height=target_height)
        
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
        # 선택된 인터페이스와 가중치 추출
        selected_items = [(ip, weight_var.get()) for var, ip, weight_var in self.ip_vars if var.get()]

        if not selected_items:
            messagebox.showerror("Error", "Select at least one IP address!")
            return

        # 명령어 준비
        command = ["go-dispatch-proxy.exe"]

        # 인터페이스별 인수 추가 (IP[@weight] 형태)
        for ip, weight in selected_items:
            arg = f"{ip}@{weight}" if weight != 1 else ip  # weight 1은 생략 가능
            command.append(arg)

        # 기타 옵션
        if self.lhost_var.get():
            command.extend(["-lhost", self.lhost_var.get()])

        if self.lport_var.get():
            command.extend(["-lport", self.lport_var.get()])

        if self.tunnel_var.get():
            command.append("-tunnel")
        
        if self.quiet_var.get():
            command.append("-quiet")
        

        try:
            # Aggior나 l'interfaccia per mostrare che stiamo avviando il proxy
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
            
            # Aggior나 lo stato
            self.running = True
            self.start_button.configure(text="Stop Proxy", fg_color="#C41E3A", hover_color="#E32636")
            
            # Avvia un thread per leggere l'output
        except FileNotFoundError as e:
            self.update_output("\n[실행 오류] go-dispatch-proxy.exe 파일을 찾을 수 없습니다.\n"
                               "실행 파일이 프로그램 폴더 또는 시스템 PATH에 있는지 확인해 주세요.\n")
            messagebox.showerror("실행 오류", "go-dispatch-proxy.exe 파일을 찾을 수 없습니다.\n"
                                 "실행 파일이 프로그램 폴더 또는 시스템 PATH에 있는지 확인해 주세요.")
        except Exception as e:
            self.update_output(f"Unable to start proxy: {str(e)}")
            messagebox.showerror("Error", f"Unable to start proxy: {str(e)}")
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
    
    # --------------------------------------------------
    # NIC statistics 업데이트
    # --------------------------------------------------
    def update_nic_stats(self):
        """Update NIC statistics table every second (physical NICs only)."""
        try:
            counters = psutil.net_io_counters(pernic=True)

            # Build header once
            if not hasattr(self, "_stats_header_built"):
                headers = ["Interface", "▲ Mb/s", "▼ Mb/s", "TX GB", "RX GB"]
                for col, text in enumerate(headers):
                    lbl = ctk.CTkLabel(self.stats_content, text=text, font=ctk.CTkFont(size=12, weight="bold"))
                    lbl.grid(row=0, column=col, padx=4, pady=(0,2), sticky="w" if col==0 else "e")
                self._stats_header_built = True

            row_idx = 1  # start after header
            for nic in getattr(self, "physical_nics", []):
                data = counters.get(nic)
                if data is None:
                    continue

                prev_sent, prev_recv = self.nic_prev_counters.get(nic, (data.bytes_sent, data.bytes_recv))
                elapsed = max(time.time() - self.last_stats_time, 1e-6)
                up_rate = (data.bytes_sent - prev_sent) * 8 / 1_000_000 / elapsed
                down_rate = (data.bytes_recv - prev_recv) * 8 / 1_000_000 / elapsed

                # Create row widgets if first time
                if nic not in self.nic_stat_labels:
                    name_lbl = ctk.CTkLabel(self.stats_content, text=nic, anchor="w")
                    up_lbl = ctk.CTkLabel(self.stats_content, anchor="e")
                    down_lbl = ctk.CTkLabel(self.stats_content, anchor="e")
                    tx_lbl = ctk.CTkLabel(self.stats_content, anchor="e")
                    rx_lbl = ctk.CTkLabel(self.stats_content, anchor="e")
                    widgets = (name_lbl, up_lbl, down_lbl, tx_lbl, rx_lbl)
                    for col, w in enumerate(widgets):
                        w.grid(row=row_idx, column=col, padx=4, sticky="w" if col==0 else "e")
                    self.nic_stat_labels[nic] = widgets
                else:
                    widgets = self.nic_stat_labels[nic]
                    # move row if ordering changed
                    for col, w in enumerate(widgets):
                        w.grid_configure(row=row_idx)

                widgets[1].configure(text=f"{up_rate:5.1f}")
                widgets[2].configure(text=f"{down_rate:5.1f}")
                widgets[3].configure(text=f"{data.bytes_sent/1_000_000_000:.2f}")
                widgets[4].configure(text=f"{data.bytes_recv/1_000_000_000:.2f}")

                self.nic_prev_counters[nic] = (data.bytes_sent, data.bytes_recv)
                row_idx += 1

            self.last_stats_time = time.time()
        except Exception as e:
            self.update_output(f"[NIC stats error] {e}\n")

        # schedule next update
        self.after(1000, self.update_nic_stats)

    
    def on_closing(self):
        """Gestisce la chiusura dell'applicazione"""
        if self.running:
            self.stop_proxy()
        
        self.destroy()

if __name__ == "__main__":
    app = GoDispatchProxyGUI()
    app.mainloop()
