import pandas as pd
import time
import random
import os
import tkinter as tk
from tkinter import StringVar, messagebox, ttk
from instagrapi import Client
from instagrapi.types import UserShort
from typing import List, Optional
import csv
import threading
from datetime import datetime

class InstagramMessenger:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Instagram Messenger")
        self.root.geometry("400x300")
        
        self.client = None
        self.load_accounts()
        self.create_login_ui()
        self.messaged_accounts_lock = threading.Lock()
        self.initialize_messaged_accounts()
    
    def load_accounts(self):
        try:
            self.accounts_df = pd.read_csv('insta_accounts.csv')
            if 'active' not in self.accounts_df.columns:
                self.accounts_df['active'] = True
                self.save_accounts()
        except FileNotFoundError:
            self.accounts_df = pd.DataFrame(columns=[
                'username', 'password', 'message_template',
                'min_followers', 'max_followers', 'active'
            ])
            default_account = {
                'username': 'jestorshaunak',
                'password': '26314921*bubu',
                'message_template': 'Hi! I love your work and would like to connect.',
                'min_followers': 1000,
                'max_followers': 50000,
                'active': True
            }
            self.accounts_df = pd.concat([
                self.accounts_df,
                pd.DataFrame([default_account])
            ], ignore_index=True)
            self.save_accounts()
    
    def save_accounts(self):
        """Safely save accounts to CSV with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.accounts_df.to_csv('insta_accounts.csv', index=False)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    messagebox.showerror("Error", f"Failed to save accounts after {max_retries} attempts: {str(e)}")
                time.sleep(1)
    
    def initialize_messaged_accounts(self):
        """Initialize or load the DataFrame for tracking messaged accounts"""
        try:
            self.messaged_df = pd.read_csv('messaged_instagram_accounts.csv')
            if 'messaged' not in self.messaged_df.columns:
                self.messaged_df['messaged'] = True  # Set all existing entries as messaged
                self.messaged_df.to_csv('messaged_instagram_accounts.csv', index=False)
        except FileNotFoundError:
            self.messaged_df = pd.DataFrame(columns=[
                'username',
                'keyword',
                'followers',
                'message_template',
                'timestamp',
                'messaged'  # New boolean column
            ])
            self.messaged_df.to_csv('messaged_instagram_accounts.csv', index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize messaged accounts: {str(e)}")
            self.messaged_df = pd.DataFrame(columns=[
                'username',
                'keyword',
                'followers',
                'message_template',
                'timestamp',
                'messaged'  # New boolean column
            ])
    
    def add_messaged_account(self, username: str, keyword: str, followers: int, message_template: str):
        """Add a new messaged account to the DataFrame and CSV"""
        try:
            # Check if user already exists
            existing_user = self.messaged_df[self.messaged_df['username'].str.lower() == username.lower()]
            
            if len(existing_user) > 0:
                # Update existing user
                self.messaged_df.loc[existing_user.index, 'messaged'] = True
                self.messaged_df.loc[existing_user.index, 'timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Add new user
                new_entry = {
                    'username': username,
                    'keyword': keyword,
                    'followers': followers,
                    'message_template': message_template,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'messaged': True
                }
                self.messaged_df = pd.concat([
                    self.messaged_df,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
            
            # Save to CSV
            self.messaged_df.to_csv('messaged_instagram_accounts.csv', index=False)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add messaged account: {str(e)}")
    
    def create_login_ui(self):
        # Login Frame
        login_frame = ttk.LabelFrame(self.root, text="Instagram Login", padding="20")
        login_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Account Selection
        ttk.Label(login_frame, text="Select Account:").grid(row=0, column=0, sticky='w', pady=5)
        self.account_var = StringVar()
        account_combo = ttk.Combobox(login_frame, textvariable=self.account_var, width=27)
        account_combo['values'] = self.accounts_df[self.accounts_df['active']]['username'].tolist()
        if len(account_combo['values']) > 0:
            account_combo.current(0)
        account_combo.grid(row=0, column=1, pady=5)
        
        # Add Account Button
        ttk.Button(login_frame, text="Add Account", command=self.add_account).grid(row=0, column=2, padx=5)
        
        # Message Template
        ttk.Label(login_frame, text="Message Template:").grid(row=1, column=0, sticky='w', pady=5)
        self.message_var = StringVar()
        ttk.Entry(login_frame, textvariable=self.message_var, width=30).grid(row=1, column=1, columnspan=2, pady=5)
        
        # Follower Range
        follower_frame = ttk.Frame(login_frame)
        follower_frame.grid(row=2, column=0, columnspan=3, pady=5)
        
        ttk.Label(follower_frame, text="Follower Range:").pack(side='left', padx=(0, 5))
        self.min_followers_var = StringVar()
        self.max_followers_var = StringVar()
        ttk.Entry(follower_frame, textvariable=self.min_followers_var, width=8).pack(side='left', padx=2)
        ttk.Label(follower_frame, text="to").pack(side='left', padx=2)
        ttk.Entry(follower_frame, textvariable=self.max_followers_var, width=8).pack(side='left', padx=2)
        
        def on_account_select(event):
            selected = self.account_var.get()
            if selected:
                account = self.accounts_df[self.accounts_df['username'] == selected].iloc[0]
                self.message_var.set(account['message_template'])
                self.min_followers_var.set(str(account['min_followers']))
                self.max_followers_var.set(str(account['max_followers']))
        
        account_combo.bind('<<ComboboxSelected>>', on_account_select)
        
        if len(account_combo['values']) > 0:
            on_account_select(None)
        
        ttk.Button(login_frame, text="Login and Start", command=self.start_messaging).grid(row=3, column=0, columnspan=3, pady=20)
    
    def search_and_message_accounts(self, keyword: str, num_accounts: int, log_message) -> int:
        accounts_messaged = 0
        max_retries = 3
        retry_delay = 5
        search_offset = 0  # Track how many users we've searched through
        max_search_attempts = 3  # Maximum number of search attempts with different offsets
        
        # Load the messaged accounts at the start to avoid repeated file reads
        try:
            messaged_df = pd.read_csv('messaged_instagram_accounts.csv')
            messaged_usernames = set(messaged_df[messaged_df['messaged'] == True]['username'].str.lower())
        except Exception as e:
            log_message(f"Warning: Could not load messaged accounts history: {e}")
            messaged_usernames = set()
        
        try:
            while accounts_messaged < num_accounts and search_offset < max_search_attempts:
                log_message(f"\nSearching for users (attempt {search_offset + 1}/{max_search_attempts})...")
                search_results = None
                
                for attempt in range(max_retries):
                    try:
                        search_results = self.client.search_users(keyword)
                        # Filter out already messaged users
                        search_results = [user for user in search_results if user.username.lower() not in messaged_usernames]
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            log_message(f"Search attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        else:
                            raise Exception(f"Failed to search users after {max_retries} attempts: {e}")
                
                if not search_results:
                    log_message("No more new users found in this search attempt")
                    search_offset += 1
                    if search_offset >= max_search_attempts:
                        log_message(f"\nNo more new users available after {max_search_attempts} search attempts.")
                        log_message(f"Successfully messaged {accounts_messaged} out of {num_accounts} requested accounts.")
                        break
                    continue
                
                log_message(f"Found {len(search_results)} new users in this batch. Starting to process...")
                
                for user in search_results:
                    if accounts_messaged >= num_accounts:
                        break
                    
                    try:
                        log_message(f"\nProcessing user: {user.username}")
                        
                        # Check if user has already been messaged
                        if user.username.lower() in messaged_usernames:
                            log_message(f"Skipping {user.username} - already messaged before")
                            continue
                            
                        time.sleep(random.uniform(3, 6))
                        
                        user_info = None
                        for attempt in range(max_retries):
                            try:
                                user_info = self.client.user_info(user.pk)
                                break
                            except Exception as e:
                                if attempt < max_retries - 1:
                                    log_message(f"User info attempt {attempt + 1} failed: {e}. Retrying...")
                                    time.sleep(retry_delay)
                                else:
                                    log_message(f"Failed to get user info after {max_retries} attempts")
                                    continue
                        
                        if not user_info:
                            continue
                        
                        followers = user_info.follower_count
                        min_followers = int(self.min_followers_var.get())
                        max_followers = int(self.max_followers_var.get())
                        
                        log_message(f"Followers: {followers}")
                        
                        if min_followers <= followers <= max_followers:
                            log_message("Follower count within range. Attempting to send message...")
                            time.sleep(random.uniform(4, 8))
                            
                            message_sent = False
                            for attempt in range(max_retries):
                                try:
                                    self.client.direct_send(
                                        self.message_var.get(),
                                        user_ids=[user.pk]
                                    )
                                    message_sent = True
                                    break
                                except Exception as e:
                                    if attempt < max_retries - 1:
                                        log_message(f"Message attempt {attempt + 1} failed: {e}. Retrying...")
                                        time.sleep(retry_delay)
                                    else:
                                        log_message(f"Failed to send message after {max_retries} attempts")
                            
                            if message_sent:
                                accounts_messaged += 1
                                log_message(f"Successfully messaged {user.username}")
                                
                                # Add to messaged accounts with messaged=True
                                self.add_messaged_account(
                                    username=user.username,
                                    keyword=keyword,
                                    followers=followers,
                                    message_template=self.message_var.get()
                                )
                                
                                # Add to our in-memory set
                                messaged_usernames.add(user.username.lower())
                                
                                time.sleep(random.uniform(5, 10))
                            else:
                                log_message("Failed to send message")
                        else:
                            log_message("Follower count outside range, skipping...")
                            
                    except Exception as e:
                        log_message(f"Error processing user: {e}")
                        continue
                
                search_offset += 1
                
        except Exception as e:
            log_message(f"Search error: {e}")
            messagebox.showerror("Error", f"An error occurred while searching: {str(e)}")
            
        if accounts_messaged < num_accounts:
            log_message(f"\nNote: Could only message {accounts_messaged} out of {num_accounts} requested accounts due to limited search results.")
            
        return accounts_messaged
    
    def login_to_instagram(self, username: str, password: str) -> bool:
        try:
            self.client = Client()
            try:
                self.client.login(username, password)
            except Exception as e:
                if "challenge_required" in str(e):
                    challenge_window = tk.Toplevel(self.root)
                    challenge_window.title("Instagram Verification")
                    challenge_window.geometry("300x150")
                    
                    challenge_window.transient(self.root)
                    challenge_window.grab_set()
                    challenge_window.attributes('-topmost', True)
                    
                    frame = ttk.Frame(challenge_window, padding="20")
                    frame.pack(fill='both', expand=True)
                    
                    ttk.Label(frame, text=f"Enter verification code sent to {username}:").pack(pady=(0, 10))
                    
                    code_var = StringVar()
                    code_entry = ttk.Entry(frame, textvariable=code_var, width=20)
                    code_entry.pack(pady=(0, 10))
                    code_entry.focus()
                    
                    def submit_code():
                        try:
                            code = code_var.get()
                            if len(code) != 6 or not code.isdigit():
                                messagebox.showerror("Error", "Please enter a valid 6-digit code")
                                return
                            self.client.login(username, password, verification_code=code)
                            challenge_window.destroy()
                        except Exception as e:
                            messagebox.showerror("Error", f"Verification failed: {str(e)}")
                    
                    def on_enter(event):
                        submit_code()
                    
                    code_entry.bind('<Return>', on_enter)
                    ttk.Button(frame, text="Submit", command=submit_code).pack()
                    
                    self.root.wait_window(challenge_window)
                    
                    if not self.client.user_id:
                        return False
                else:
                    raise e
            
            return True
        except Exception as e:
            print(f"Login error: {e}")
            messagebox.showerror("Login Error", str(e))
            return False
    
    def start_messaging(self):
        username = self.account_var.get()
        if not username:
            messagebox.showwarning("Error", "Please select an account")
            return
        
        account_idx = self.accounts_df[self.accounts_df['username'] == username].index[0]
        
        self.accounts_df.loc[account_idx, 'message_template'] = self.message_var.get()
        self.accounts_df.loc[account_idx, 'min_followers'] = int(self.min_followers_var.get())
        self.accounts_df.loc[account_idx, 'max_followers'] = int(self.max_followers_var.get())
        self.save_accounts()
        
        messaging_window = tk.Toplevel(self.root)
        messaging_window.title("Instagram Messenger")
        messaging_window.geometry("500x400")
        
        frame = ttk.Frame(messaging_window, padding="20")
        frame.pack(fill='both', expand=True)
        
        settings_frame = ttk.LabelFrame(frame, text="Search Settings", padding="10")
        settings_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(settings_frame, text="Search Keyword:").pack(side='left', padx=(0, 5))
        keyword_var = StringVar()
        ttk.Entry(settings_frame, textvariable=keyword_var, width=20).pack(side='left', padx=(0, 10))
        
        ttk.Label(settings_frame, text="Number of Accounts:").pack(side='left', padx=(0, 5))
        num_accounts_var = tk.IntVar(value=10)
        ttk.Entry(settings_frame, textvariable=num_accounts_var, width=5).pack(side='left')
        
        log_frame = ttk.LabelFrame(frame, text="Progress Log", padding="10")
        log_frame.pack(fill='both', expand=True)
        
        log_text = tk.Text(log_frame, height=15, width=50, wrap=tk.WORD)
        log_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=log_text.yview)
        scrollbar.pack(side='right', fill='y')
        log_text.configure(yscrollcommand=scrollbar.set)
        
        def log_message(message):
            log_text.insert(tk.END, f"{message}\n")
            log_text.see(tk.END)
            messaging_window.update()
        
        def start():
            keyword = keyword_var.get()
            num_accounts = num_accounts_var.get()
            
            if not keyword:
                messagebox.showwarning("Error", "Please enter a search keyword")
                return
            
            log_message(f"Starting messaging process for account: {username}")
            log_message(f"Search keyword: {keyword}")
            log_message(f"Target accounts: {num_accounts}")
            
            if self.login_to_instagram(username, self.accounts_df[self.accounts_df['username'] == username].iloc[0]['password']):
                log_message("Successfully logged in to Instagram")
                accounts_messaged = self.search_and_message_accounts(keyword, num_accounts, log_message)
                log_message(f"Messaging completed. Attempted to message {accounts_messaged} accounts.")
                messagebox.showinfo("Complete", f"Messaging completed. Attempted to message {accounts_messaged} accounts.")
            else:
                log_message("Failed to login to Instagram")
        
        ttk.Button(frame, text="Start Messaging", command=start).pack(pady=10)
    
    def add_account(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Instagram Account")
        add_window.geometry("300x250")
        
        frame = ttk.Frame(add_window, padding="20")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Username:").pack(pady=(0, 5))
        username_var = StringVar()
        ttk.Entry(frame, textvariable=username_var, width=30).pack(pady=(0, 10))
        
        ttk.Label(frame, text="Password:").pack(pady=(0, 5))
        password_var = StringVar()
        ttk.Entry(frame, textvariable=password_var, width=30, show="*").pack(pady=(0, 10))
        
        ttk.Label(frame, text="Message Template:").pack(pady=(0, 5))
        message_var = StringVar(value="Hi! I love your work and would like to connect.")
        ttk.Entry(frame, textvariable=message_var, width=30).pack(pady=(0, 10))
        
        ttk.Label(frame, text="Follower Range:").pack(pady=(0, 5))
        range_frame = ttk.Frame(frame)
        range_frame.pack(pady=(0, 10))
        
        min_var = StringVar(value="1000")
        max_var = StringVar(value="50000")
        ttk.Entry(range_frame, textvariable=min_var, width=8).pack(side='left', padx=2)
        ttk.Label(range_frame, text="to").pack(side='left', padx=2)
        ttk.Entry(range_frame, textvariable=max_var, width=8).pack(side='left', padx=2)
        
        def save_account():
            new_account = {
                'username': username_var.get(),
                'password': password_var.get(),
                'message_template': message_var.get(),
                'min_followers': int(min_var.get()),
                'max_followers': int(max_var.get()),
                'active': True
            }
            
            self.accounts_df = pd.concat([
                self.accounts_df,
                pd.DataFrame([new_account])
            ], ignore_index=True)
            self.save_accounts()
            
            account_combo = self.root.winfo_children()[0].winfo_children()[0].winfo_children()[1]
            account_combo['values'] = self.accounts_df[self.accounts_df['active']]['username'].tolist()
            account_combo.set(new_account['username'])
            
            add_window.destroy()
        
        ttk.Button(frame, text="Save Account", command=save_account).pack(pady=10)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    messenger = InstagramMessenger()
    messenger.run() 