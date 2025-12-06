"""Tkinter GUI for inwebstigate."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from typing import Optional
from agent import WebInvestigationAgent
from config import Config


class InwebstigateGUI:
    """Tkinter GUI for the web investigation tool."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Inwebstigate - AI Web Investigator")
        self.root.geometry("1200x800")
        
        # Agent
        self.agent: Optional[WebInvestigationAgent] = None
        self.investigation_thread: Optional[threading.Thread] = None
        self.is_investigating = False
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_container,
            text="🔍 Inwebstigate - AI-Powered Web Investigation",
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky=tk.W)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_container, text="Investigation Settings", padding="10")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        # Query input
        ttk.Label(input_frame, text="Query:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.query_entry = ttk.Entry(input_frame, width=80)
        self.query_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Starting URL input
        ttk.Label(input_frame, text="Start URL (optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(input_frame, width=80)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.url_entry.insert(0, "https://")
        
        # LLM Provider selection
        llm_frame = ttk.Frame(input_frame)
        llm_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(llm_frame, text="LLM Provider:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.llm_var = tk.StringVar(value=Config.LLM_PROVIDER)
        ollama_radio = ttk.Radiobutton(llm_frame, text="Ollama (Local)", variable=self.llm_var, value="ollama")
        ollama_radio.pack(side=tk.LEFT, padx=5)
        
        groq_radio = ttk.Radiobutton(llm_frame, text="Groq (Cloud)", variable=self.llm_var, value="groq")
        groq_radio.pack(side=tk.LEFT, padx=5)
        
        # Max depth
        ttk.Label(llm_frame, text="Max Pages:").pack(side=tk.LEFT, padx=(20, 5))
        self.max_depth_var = tk.StringVar(value=str(Config.MAX_NAVIGATION_DEPTH))
        max_depth_spinbox = ttk.Spinbox(llm_frame, from_=1, to=10, width=5, textvariable=self.max_depth_var)
        max_depth_spinbox.pack(side=tk.LEFT)
        
        # Start button
        self.start_button = ttk.Button(
            input_frame,
            text="🚀 Start Investigation",
            command=self._start_investigation,
            style='Accent.TButton'
        )
        self.start_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Stop button
        self.stop_button = ttk.Button(
            input_frame,
            text="⏹ Stop Investigation",
            command=self._stop_investigation,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_container, text="Investigation Progress", padding="10")
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready to investigate")
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Output frame with tabs
        output_frame = ttk.Frame(main_container)
        output_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(output_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Navigation Log Tab
        nav_frame = ttk.Frame(self.notebook)
        self.notebook.add(nav_frame, text="📍 Navigation Log")
        nav_frame.columnconfigure(0, weight=1)
        nav_frame.rowconfigure(0, weight=1)
        
        self.nav_log = scrolledtext.ScrolledText(
            nav_frame,
            wrap=tk.WORD,
            width=100,
            height=25,
            font=('Courier', 10)
        )
        self.nav_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Configure text tags for colored output
        self.nav_log.tag_config('url', foreground='blue')
        self.nav_log.tag_config('finding', foreground='green')
        self.nav_log.tag_config('error', foreground='red')
        self.nav_log.tag_config('decision', foreground='purple')
        self.nav_log.tag_config('header', foreground='darkblue', font=('Courier', 10, 'bold'))
        
        # Path Tree Tab
        tree_frame = ttk.Frame(self.notebook)
        self.notebook.add(tree_frame, text="🗺️ Investigation Path")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Create Treeview
        self.path_tree = ttk.Treeview(tree_frame, columns=('URL', 'Findings'), show='tree headings')
        self.path_tree.heading('#0', text='Step')
        self.path_tree.heading('URL', text='URL')
        self.path_tree.heading('Findings', text='Key Findings')
        self.path_tree.column('#0', width=100)
        self.path_tree.column('URL', width=400)
        self.path_tree.column('Findings', width=600)
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.path_tree.yview)
        self.path_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.path_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0), pady=5)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S), pady=5, padx=(0, 5))
        
        # Final Answer Tab
        answer_frame = ttk.Frame(self.notebook)
        self.notebook.add(answer_frame, text="✨ Final Answer")
        answer_frame.columnconfigure(0, weight=1)
        answer_frame.rowconfigure(0, weight=1)
        
        self.answer_text = scrolledtext.ScrolledText(
            answer_frame,
            wrap=tk.WORD,
            width=100,
            height=25,
            font=('Helvetica', 11)
        )
        self.answer_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Status bar
        self.status_bar = ttk.Label(
            main_container,
            text=f"LLM Provider: {Config.LLM_PROVIDER.upper()} | Ready",
            relief=tk.SUNKEN
        )
        self.status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def _start_investigation(self):
        """Start the investigation in a separate thread."""
        query = self.query_entry.get().strip()
        
        if not query:
            messagebox.showwarning("Input Required", "Please enter a query to investigate.")
            return
        
        # Get start URL
        start_url = self.url_entry.get().strip()
        if start_url == "https://" or start_url == "http://":
            start_url = None
        
        # Get max depth
        try:
            max_depth = int(self.max_depth_var.get())
        except ValueError:
            max_depth = Config.MAX_NAVIGATION_DEPTH
        
        # Clear previous results
        self.nav_log.delete(1.0, tk.END)
        self.answer_text.delete(1.0, tk.END)
        for item in self.path_tree.get_children():
            self.path_tree.delete(item)
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)
        self.is_investigating = True
        
        # Start investigation in separate thread
        self.investigation_thread = threading.Thread(
            target=self._run_investigation,
            args=(query, start_url, max_depth),
            daemon=True
        )
        self.investigation_thread.start()
    
    def _run_investigation(self, query: str, start_url: Optional[str], max_depth: int):
        """Run the investigation (called in separate thread)."""
        try:
            # Create agent with callback
            llm_provider = self.llm_var.get()
            self.agent = WebInvestigationAgent(llm_provider, self._progress_callback)
            
            # Run investigation
            final_answer = self.agent.investigate(query, start_url, max_depth)
            
            # Display final answer
            self.root.after(0, self._display_final_answer, final_answer)
            
        except Exception as e:
            error_msg = f"Error during investigation: {str(e)}"
            self.root.after(0, self._log_to_nav, f"❌ {error_msg}\n", 'error')
            messagebox.showerror("Investigation Error", error_msg)
        finally:
            self.root.after(0, self._investigation_complete)
    
    def _progress_callback(self, message: str, data: Optional[dict] = None):
        """Callback for progress updates from the agent."""
        if not self.is_investigating:
            return
        
        # Update UI in main thread
        self.root.after(0, self._update_progress_ui, message, data)
    
    def _update_progress_ui(self, message: str, data: Optional[dict]):
        """Update progress UI elements."""
        # Update progress label
        self.progress_label.config(text=message[:100])
        
        # Log to navigation log
        if data:
            msg_type = data.get('type', '')
            
            if msg_type == 'navigation':
                self._log_to_nav(f"\n{'='*80}\n", 'header')
                self._log_to_nav(f"Step {data['depth']}/{data['max_depth']}: ", 'header')
                self._log_to_nav(f"{data['url']}\n", 'url')
            
            elif msg_type == 'page_loaded':
                self._log_to_nav(f"✅ Loaded: {data['title']}\n", 'finding')
                self._log_to_nav(f"   Found {data['links_found']} links\n")
            
            elif msg_type == 'findings':
                self._log_to_nav(f"\n📝 Findings:\n", 'finding')
                self._log_to_nav(f"{data['findings']}\n\n")
                
                # Add to tree
                step_num = len(self.path_tree.get_children()) + 1
                self.path_tree.insert(
                    '',
                    'end',
                    text=f"Step {step_num}",
                    values=(data['url'], data['findings'][:100] + '...')
                )
            
            elif msg_type == 'next_link':
                self._log_to_nav(f"\n➡️  Next Link: ", 'decision')
                self._log_to_nav(f"{data['url']}\n", 'url')
                self._log_to_nav(f"💡 Reason: {data['reason']}\n", 'decision')
            
            elif msg_type == 'error':
                self._log_to_nav(f"❌ Error: {data['error']}\n", 'error')
            
            elif msg_type == 'stop':
                self._log_to_nav(f"\n🛑 {data['reason']}\n", 'decision')
        else:
            self._log_to_nav(message + "\n")
        
        # Update status bar
        pages_visited = len(self.path_tree.get_children())
        self.status_bar.config(text=f"Investigating... | Pages visited: {pages_visited}")
    
    def _log_to_nav(self, text: str, tag: Optional[str] = None):
        """Log text to navigation log."""
        self.nav_log.insert(tk.END, text, tag)
        self.nav_log.see(tk.END)
    
    def _display_final_answer(self, answer: str):
        """Display the final answer."""
        self.answer_text.delete(1.0, tk.END)
        self.answer_text.insert(1.0, answer)
        
        # Switch to final answer tab
        self.notebook.select(2)
        
        self._log_to_nav(f"\n{'='*80}\n", 'header')
        self._log_to_nav("✨ FINAL ANSWER:\n", 'header')
        self._log_to_nav(f"{answer}\n")
    
    def _stop_investigation(self):
        """Stop the current investigation."""
        self.is_investigating = False
        self._investigation_complete()
        self._log_to_nav("\n⏹ Investigation stopped by user\n", 'error')
    
    def _investigation_complete(self):
        """Called when investigation is complete."""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.is_investigating = False
        
        pages_visited = len(self.path_tree.get_children())
        self.status_bar.config(text=f"Investigation complete | Pages visited: {pages_visited}")
        self.progress_label.config(text="Investigation complete!")
        
        # Cleanup agent
        if self.agent:
            self.agent.cleanup()
            self.agent = None
    
    def cleanup(self):
        """Clean up resources."""
        self.is_investigating = False
        if self.agent:
            self.agent.cleanup()


def main():
    """Main entry point for GUI."""
    root = tk.Tk()
    app = InwebstigateGUI(root)
    
    # Handle window close
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

