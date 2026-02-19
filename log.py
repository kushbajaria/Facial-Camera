import csv
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

class SimpleLogger:
    def __init__(self, log_file="visitor_log.csv"):
        self.log_file = log_file
        self.create_log_file()
    
    def create_log_file(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Name', 'Action', 'Event Type'])
    
    def log_event(self, name, action, event_type="FACE_DETECTED"):
        """Log an event to CSV file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, name, action, event_type])
        
        return timestamp

class LogViewerWindow:
    def __init__(self, parent, logger):
        self.logger = logger
        self.window = tk.Toplevel(parent)
        self.window.title("Visitor Log")
        self.window.geometry("700x400")
        
        self.window.configure(bg='#2c3e50')
        self.setup_ui()
        self.load_logs()
    
    def setup_ui(self):
        title = tk.Label(self.window, text="📋 Door Access Log", 
                        font=("Arial", 16, "bold"), 
                        bg='#2c3e50', fg='white')
        title.pack(pady=10)
        
        frame = tk.Frame(self.window, bg='#2c3e50')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('Time', 'Name', 'Action', 'Event')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('Time', text='Timestamp')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Action', text='Action Taken')
        self.tree.heading('Event', text='Event Type')
        
        self.tree.column('Time', width=150)
        self.tree.column('Name', width=150)
        self.tree.column('Action', width=120)
        self.tree.column('Event', width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        button_frame = tk.Frame(self.window, bg='#2c3e50')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        refresh_btn = tk.Button(button_frame, text="🔄 Refresh", 
                        command=self.load_logs,
                        bg='#3498db', fg='white',
                            font=("Arial", 10))
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(button_frame, text="📥 Export CSV", 
                        command=self.export_logs,
                        bg='#27ae60', fg='white',
                        font=("Arial", 10))
        export_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(button_frame, text="🗑️ Clear Log", 
                        command=self.clear_logs,
                        bg='#e74c3c', fg='white',
                        font=("Arial", 10))
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(button_frame, text="", 
                                bg='#2c3e50', fg='#ecf0f1')
        self.status_label.pack(side=tk.RIGHT, padx=5)
    
    def load_logs(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            with open(self.logger.log_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                rows = list(reader)
                for row in reversed(rows):
                    if row and len(row) >= 4:
                        tags = ()
                        if row[3] == "STRANGER_ALERT":
                            tags = ('stranger',)
                        elif row[2] == "UNLOCK":
                            tags = ('unlock',)
                        self.tree.insert('', tk.END, values=row, tags=tags)
            
            self.tree.tag_configure('stranger', background='#ffcccc')
            self.tree.tag_configure('unlock', background='#ccffcc')
            
            self.status_label.config(text=f"✅ Loaded {len(rows)} entries")
        except FileNotFoundError:
            self.status_label.config(text="📂 No log file yet")
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}")
    
    def export_logs(self):
        try:
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_name = f"visitor_log_backup_{timestamp}.csv"
            shutil.copy2(self.logger.log_file, export_name)
            self.status_label.config(text=f"✅ Exported to {export_name}")
            messagebox.showinfo("Success", f"Logs exported to {export_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def clear_logs(self):
        if messagebox.askyesno("Confirm", "Delete all logs? This cannot be undone."):
            try:
                with open(self.logger.log_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Name', 'Action', 'Event Type'])
                self.load_logs()
                self.status_label.config(text="✅ Log cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear: {str(e)}")
