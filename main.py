import tkinter as tk
from tkinter import ttk, messagebox
import random
import sqlite3
import os
from datetime import date, datetime, timedelta
import threading
import time
from collections import defaultdict
import queue

class EntertainmentSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Entertainment Selector")
        self.root.geometry("700x800")
        self.root.configure(bg='#1a1a2e')
        
        # Thread-safe database path
        self.db_path = 'entertainment_app.db'
        
        # Thread communication
        self.db_queue = queue.Queue()
        
        # Data
        self.choices = ["PC", "PS5", "Odin 2", "Book", "Meta Quest 3", 
                       "LeetCode", "Nintendo Switch", "RG353V", "Anime"]
        self.weights = [1, 1, 0.7, 1, 0.2, 1, 0.5, 0.2, 0.7]
        self.current_selection = None
        self.is_selecting = False
        
        # Initialize database in main thread
        self.setup_database()
        
        # Create GUI
        self.create_widgets()
        
    def setup_database(self):
        """Setup SQLite database - main thread only"""
        try:
            print(f"Setting up database: {self.db_path}")
            
            # Create connection in main thread
            self.main_conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.main_conn.cursor()
            
            # Create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS selections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT NOT NULL,
                    selection_date TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            self.main_conn.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"Database error: {e}")
            messagebox.showerror("Database Error", f"Could not initialize database: {e}")
    
    def get_db_connection(self):
        """Get a thread-safe database connection"""
        return sqlite3.connect(self.db_path)
            
    def create_widgets(self):
        """Create all GUI widgets with better colors"""
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title section
        title_frame = tk.Frame(main_frame, bg='#1a1a2e')
        title_frame.pack(fill='x', pady=(0, 30))
        
        title_label = tk.Label(title_frame, text="🎮 Entertainment Selector", 
                              bg='#1a1a2e', fg='#0078d4', 
                              font=('Arial', 24, 'bold'))
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="Let fate decide your entertainment!", 
                                 bg='#1a1a2e', fg='#0078d4', 
                                 font=('Arial', 12))
        subtitle_label.pack(pady=(5, 0))
        
        # Selection display area
        selection_frame = tk.Frame(main_frame, bg='#16213e', relief='raised', bd=3)
        selection_frame.pack(fill='x', pady=20)
        
        self.selection_var = tk.StringVar(value="Click 'Choose for Me!' to start")
        self.selection_label = tk.Label(selection_frame, textvariable=self.selection_var,
                                       bg='#16213e', fg='#00d4ff', 
                                       font=('Arial', 18, 'bold'),
                                       wraplength=600, justify='center')
        self.selection_label.pack(pady=30)
        
        self.date_label = tk.Label(selection_frame, text=f"Today: {date.today()}", 
                                  bg='#16213e', fg='#888888', 
                                  font=('Arial', 10))
        self.date_label.pack(pady=(0, 15))
        
        # Mode selection
        mode_frame = tk.Frame(main_frame, bg='#1a1a2e')
        mode_frame.pack(pady=20)
        
        tk.Label(mode_frame, text="Selection Mode:", 
                bg='#1a1a2e', fg='#0078d4', font=('Arial', 12, 'bold')).pack(side='left')
        
        self.mode_var = tk.StringVar(value="normal")
        
        # Style the combobox
        style.configure('Custom.TCombobox',
                       fieldbackground='#16213e',
                       background='#16213e',
                       foreground='#0078d4',
                       arrowcolor='#00d4ff')
        
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, 
                                 values=["normal", "variety_boost", "avoid_recent"],
                                 state='readonly', font=('Arial', 11), width=15,
                                 style='Custom.TCombobox')
        mode_combo.pack(side='left', padx=(10, 0))
        
        # Control buttons with better colors
        button_frame = tk.Frame(main_frame, bg='#1a1a2e')
        button_frame.pack(pady=20)
        
        self.select_btn = tk.Button(button_frame, text="🎲 Choose for Me!",
                   command=self.start_selection,
                   bg='#0078d4', fg='#ffffff',
                   activebackground='#106ebe',
                   activeforeground='#ffffff',
                   font=('Arial', 14, 'bold'),
                   padx=25, pady=12, relief='raised', bd=2,
                   cursor='hand2')
        self.select_btn.pack(side='left', padx=10)
        
        self.save_btn = tk.Button(button_frame, text="💾 Save Choice", 
                    command=self.save_selection,
                    bg='#107c10', fg='#ffffff',
                    activebackground='#0e6d0e',
                    activeforeground='#ffffff',
                    font=('Arial', 12, 'bold'),
                    padx=20, pady=10, relief='raised', bd=2,
                    state='disabled', cursor='hand2')
        self.save_btn.pack(side='left', padx=10)
            
        stats_btn = tk.Button(button_frame, text="📊 View Stats", 
                    command=self.show_stats,
                    bg='#881798', fg='#ffffff',
                    activebackground='#7a1589',
                    activeforeground='#ffffff',
                    font=('Arial', 12, 'bold'),
                    padx=20, pady=10, relief='raised', bd=2,
                    cursor='hand2')
        stats_btn.pack(side='left', padx=10)
        
        # History section
        history_frame = tk.LabelFrame(main_frame, text=" Recent Selections ", 
                                     bg='#1a1a2e', fg='#0078d4',
                                     font=('Arial', 14, 'bold'))
        history_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # History display
        text_frame = tk.Frame(history_frame, bg='#1a1a2e')
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.history_text = tk.Text(text_frame, height=6, 
                                   bg='#16213e', fg='#0078d4',
                                   font=('Arial', 10), wrap='word',
                                   state='disabled', relief='sunken', bd=2,
                                   insertbackground='#00d4ff')
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', 
                                 command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        
        self.history_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Load initial history
        self.update_history_display()
        
    def get_recent_selections(self, days_back=7):
        """Get recent selections from database - thread safe"""
        try:
            # Create new connection for this thread
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cutoff_date = date.today() - timedelta(days=days_back)
            cursor.execute("""
                SELECT item, selection_date, timestamp 
                FROM selections 
                WHERE selection_date >= ? 
                ORDER BY timestamp DESC
            """, (str(cutoff_date),))
            
            results = cursor.fetchall()
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error getting recent selections: {e}")
            return []
    
    def calculate_weights(self):
        """Calculate weights based on selected mode"""
        mode = self.mode_var.get()
        
        if mode == "normal":
            return self.weights.copy()
        
        recent_selections = self.get_recent_selections()
        
        if mode == "avoid_recent":
            recent_items = {item for item, _, _ in recent_selections}
            weights = []
            for i, choice in enumerate(self.choices):
                if choice in recent_items:
                    weights.append(0.1)  # Very low weight instead of 0
                else:
                    weights.append(self.weights[i])
            return weights
            
        elif mode == "variety_boost":
            recent_counts = defaultdict(int)
            for item, _, _ in recent_selections:
                recent_counts[item] += 1
            
            max_count = max(recent_counts.values()) if recent_counts else 1
            weights = []
            
            for i, choice in enumerate(self.choices):
                base_weight = self.weights[i]
                count = recent_counts.get(choice, 0)
                penalty = (count / max_count) * 0.6
                adjusted = base_weight * (1 - penalty)
                weights.append(max(adjusted, base_weight * 0.2))
            
            return weights
        
        return self.weights.copy()
    
    def start_selection(self):
        """Start the selection process"""
        if self.is_selecting:
            return
            
        # Update UI immediately
        self.is_selecting = True
        self.select_btn.config(state='disabled', text="🎲 Selecting...", bg='#666666')
        self.save_btn.config(state='disabled')
        
        # Start animation and selection
        self.animate_selection()
    
    def animate_selection(self, step=0):
        """Animate selection process using after() instead of threads"""
        animation_chars = ["🎯", "🎲", "🎮", "📚", "🎭", "💻", "🎪", "🎨"]
        
        if step < 12:  # 12 animation steps
            char = animation_chars[step % len(animation_chars)]
            self.selection_var.set(f"Selecting... {char}")
            # Schedule next animation step
            self.root.after(100, lambda: self.animate_selection(step + 1))
        else:
            # Animation done, perform selection
            self.perform_selection()
    
    def perform_selection(self):
        """Perform the actual selection"""
        try:
            weights = self.calculate_weights()
            self.current_selection = random.choices(self.choices, weights=weights, k=1)[0]
            
            # Update UI
            self.selection_var.set(f"🎉 {self.current_selection} 🎉")
            self.select_btn.config(state='normal', text="🎲 Choose Again!", bg='#0078d4')
            self.save_btn.config(state='normal')
            
        except Exception as e:
            messagebox.showerror("Selection Error", f"Could not make selection: {e}")
            self.select_btn.config(state='normal', text="🎲 Choose for Me!", bg='#0078d4')
        
        finally:
            self.is_selecting = False
    
    def save_selection(self):
        """Save current selection to database with overwrite warning"""
        if not self.current_selection:
            return
            
        try:
            # Use a new connection for this operation
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            today = str(date.today())
            
            # Check if there's already a selection for today
            cursor.execute("""
                SELECT item, timestamp FROM selections 
                WHERE selection_date = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (today,))
            
            existing_record = cursor.fetchone()
            
            if existing_record:
                existing_item, existing_time = existing_record
                try:
                    formatted_time = datetime.fromisoformat(existing_time).strftime('%H:%M')
                except:
                    formatted_time = "earlier"
                
                # Show warning dialog
                result = messagebox.askyesno(
                    "⚠️ Overwrite Today's Selection?",
                    f"You already selected '{existing_item}' today ({formatted_time}).\n\n"
                    f"Do you want to overwrite it with '{self.current_selection}'?",
                    icon='warning'
                )
                
                if not result:  # User clicked No
                    return
                
                # Delete existing record for today
                cursor.execute("""
                    DELETE FROM selections WHERE selection_date = ?
                """, (today,))
            
            # Insert new record
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO selections (item, selection_date, timestamp)
                VALUES (?, ?, ?)
            """, (self.current_selection, today, timestamp))
            
            conn.commit()
            conn.close()
            
            # UI feedback
            original_text = self.save_btn.cget('text')
            original_color = self.save_btn.cget('bg')
            
            if existing_record:
                self.save_btn.config(text="🔄 Overwritten!", state='disabled', bg='#d17c00')
                success_message = f"'{self.current_selection}' has overwritten today's previous selection!"
            else:
                self.save_btn.config(text="✅ Saved!", state='disabled', bg='#0e6d0e')
                success_message = f"'{self.current_selection}' saved to history!"
            
            # Reset button after 2 seconds
            self.root.after(2000, lambda: self.save_btn.config(
                text=original_text, state='normal', bg=original_color))
            
            # Update history
            self.update_history_display()
            
            messagebox.showinfo("Success", success_message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save selection: {e}")
    
    def update_history_display(self):
        """Update the history text display"""
        try:
            recent = self.get_recent_selections(10)
            
            self.history_text.config(state='normal')
            self.history_text.delete(1.0, tk.END)
            
            if recent:
                for item, sel_date, timestamp in recent:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime('%m/%d %H:%M')
                    except:
                        time_str = sel_date
                    
                    self.history_text.insert(tk.END, f"• {item} ({time_str})\n")
            else:
                self.history_text.insert(tk.END, "No selections yet. Make your first choice!")
            
            self.history_text.config(state='disabled')
            
        except Exception as e:
            print(f"Error updating history: {e}")
    
    def show_stats(self):
        """Show statistics window"""
        try:
            # Use new connection for stats
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item, COUNT(*) as count 
                FROM selections 
                GROUP BY item 
                ORDER BY count DESC
            """)
            stats = cursor.fetchall()
            conn.close()
            
            # Create stats window with better colors
            stats_win = tk.Toplevel(self.root)
            stats_win.title("📊 Statistics")
            stats_win.geometry("400x500")
            stats_win.configure(bg='#1a1a2e')
            
            # Title
            tk.Label(stats_win, text="📊 Selection Statistics", 
                    bg='#1a1a2e', fg='#0078d4', 
                    font=('Arial', 18, 'bold')).pack(pady=20)
            
            if stats:
                # Stats frame
                stats_frame = tk.Frame(stats_win, bg='#1a1a2e')
                stats_frame.pack(fill='both', expand=True, padx=20)
                
                for item, count in stats:
                    row = tk.Frame(stats_frame, bg='#16213e', relief='raised', bd=1)
                    row.pack(fill='x', pady=2)
                    
                    tk.Label(row, text=item, bg='#16213e', fg='#0078d4', 
                            font=('Arial', 11), anchor='w').pack(side='left', padx=10, pady=5)
                    tk.Label(row, text=f"{count} times", bg='#16213e', fg='#00d4ff', 
                            font=('Arial', 11, 'bold')).pack(side='right', padx=10, pady=5)
            else:
                tk.Label(stats_win, text="No statistics available yet!", 
                        bg='#1a1a2e', fg='#0078d4', 
                        font=('Arial', 14)).pack(expand=True)
            
            # Close button
            tk.Button(stats_win, text="Close", command=stats_win.destroy,
                     bg='#d13438', fg='#0078d4', font=('Arial', 12, 'bold'),
                     activebackground='#b92b2f', activeforeground='#0078d4',
                     padx=20, pady=5, cursor='hand2').pack(pady=20)
                     
        except Exception as e:
            messagebox.showerror("Error", f"Could not load statistics: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'main_conn'):
                self.main_conn.close()
        except:
            pass

def main():
    root = tk.Tk()
    app = EntertainmentSelectorApp(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Handle close
    def on_close():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    print("Starting Entertainment Selector...")
    print("Thread-safe database operations with better UI colors")
    
    try:
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        app.cleanup()

if __name__ == "__main__":
    main()