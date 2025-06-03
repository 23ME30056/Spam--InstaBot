import pandas as pd
import time
import random
import os
import tkinter as tk
from tkinter import StringVar, messagebox, ttk
from instagrapi import Client
from instagrapi.types import UserShort
from typing import List, Optional

class InstagramMessenger:
    def __init__(self):
        # Initialize accounts DataFrame
        self.initialize_accounts()
        
        # Initialize messaged accounts DataFrame
        self.initialize_messaged_accounts()
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Instagram Messenger")
        
        # Create UI components
        self.create_ui()
        
        # Initialize Instagrapi client
        self.client = None
        
    def initialize_accounts(self):
        try:
            self.acc_df = pd.read_csv('instagram_accounts.csv')
            if 'active' not in self.acc_df.columns:
                self.acc_df['active'] = True
        except FileNotFoundError:
            self.acc_df = pd.DataFrame(columns=[
                'username', 'password', 
                'message_template', 
                'min_followers', 'max_followers', 
                'active'
            ])
            # Add a default account
            default_account = {
                'username': 'jestorshaunak',
                'password': '26314921*bubu',
                'message_template': 'Hi! I love your work and would like to connect.',
                'min_followers': 1000,
                'max_followers': 50000,
                'active': True
            }
            self.acc_df = pd.concat([
                self.acc_df, 
                pd.DataFrame([default_account])
            ], ignore_index=True)
            self.acc_df.to_csv('instagram_accounts.csv', index=False)
    
    def initialize_messaged_accounts(self):
        try:
            self.messaged_df = pd.read_csv('messaged_accounts.csv')
        except FileNotFoundError:
            self.messaged_df = pd.DataFrame(columns=[
                'username', 'keyword', 'followers', 
                'message_template', 'timestamp'
            ])
            self.messaged_df.to_csv('messaged_accounts.csv', index=False)
    
    def create_ui(self):
        # Search and Message Frame
        search_frame = ttk.LabelFrame(self.root, text="Instagram Search and Message")
        search_frame.pack(padx=10, pady=10, fill='x')
        
        # Search Keyword
        ttk.Label(search_frame, text="Search Keyword:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.keyword_var = StringVar()
        ttk.Entry(search_frame, textvariable=self.keyword_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Number of Accounts to Message
        ttk.Label(search_frame, text="Number of Accounts:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.num_accounts_var = tk.IntVar(value=10)
        ttk.Entry(search_frame, textvariable=self.num_accounts_var, width=10).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Start Messaging Button
        ttk.Button(search_frame, text="Start Messaging", command=self.start_messaging).grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        # Settings Button
        ttk.Button(self.root, text="Manage Accounts", command=self.open_account_settings).pack(pady=5)
    
    def human_like_delay(self, min_time=1, max_time=3):
        """Add a random delay to mimic human behavior"""
        delay = random.uniform(min_time, max_time)
        time.sleep(delay)
    
    def login_to_instagram(self, username: str, password: str) -> bool:
        try:
            self.client = Client()
            
            # Handle login challenge
            try:
                self.client.login(username, password)
            except Exception as e:
                if "challenge_required" in str(e):
                    # Create a dialog for verification code
                    challenge_window = tk.Toplevel(self.root)
                    challenge_window.title("Instagram Verification")
                    challenge_window.geometry("300x150")  # Set window size
                    
                    # Center the window
                    challenge_window.transient(self.root)
                    challenge_window.grab_set()
                    
                    # Make sure the window stays on top
                    challenge_window.attributes('-topmost', True)
                    
                    # Create and pack widgets
                    frame = ttk.Frame(challenge_window, padding="20")
                    frame.pack(fill='both', expand=True)
                    
                    ttk.Label(frame, text=f"Enter verification code sent to {username}:").pack(pady=(0, 10))
                    
                    code_var = StringVar()
                    code_entry = ttk.Entry(frame, textvariable=code_var, width=20)
                    code_entry.pack(pady=(0, 10))
                    code_entry.focus()  # Set focus to the entry widget
                    
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
                    
                    # Bind Enter key to submit
                    code_entry.bind('<Return>', on_enter)
                    
                    ttk.Button(frame, text="Submit", command=submit_code).pack()
                    
                    # Wait for the window to be closed
                    self.root.wait_window(challenge_window)
                    
                    # Check if login was successful
                    if not self.client.user_id:
                        return False
                else:
                    raise e
            
            return True
        except Exception as e:
            print(f"Login error: {e}")
            messagebox.showerror("Login Error", str(e))
            return False
    
    def search_and_message_accounts(self, keyword: str, num_accounts: int, account_data: dict) -> int:
        accounts_messaged = 0
        max_retries = 3
        retry_delay = 5  # seconds
        
        try:
            # Search for users with retry logic
            search_results = None
            for attempt in range(max_retries):
                try:
                    search_results = self.client.search_users(keyword)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Search attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        raise Exception(f"Failed to search users after {max_retries} attempts: {e}")
            
            if not search_results:
                print("No search results found")
                return accounts_messaged
            
            for user in search_results:
                if accounts_messaged >= num_accounts:
                    break
                
                try:
                    # Add longer delay between user info requests
                    self.human_like_delay(3, 6)
                    
                    # Get user info with retry logic
                    user_info = None
                    for attempt in range(max_retries):
                        try:
                            user_info = self.client.user_info(user.pk)
                            break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                print(f"User info attempt {attempt + 1} failed for {user.username}: {e}. Retrying in {retry_delay} seconds...")
                                time.sleep(retry_delay)
                            else:
                                print(f"Failed to get user info for {user.username} after {max_retries} attempts: {e}")
                                continue
                    
                    if not user_info:
                        continue
                    
                    followers = user_info.follower_count
                    
                    # Check if followers are within range
                    if (int(account_data['min_followers']) <= followers <= int(account_data['max_followers'])):
                        # Add longer delay before sending message
                        self.human_like_delay(4, 8)
                        
                        # Send message with retry logic
                        message_sent = False
                        for attempt in range(max_retries):
                            try:
                                self.client.direct_send(
                                    account_data['message_template'],
                                    user_ids=[user.pk]
                                )
                                message_sent = True
                                break
                            except Exception as e:
                                if attempt < max_retries - 1:
                                    print(f"Message attempt {attempt + 1} failed for {user.username}: {e}. Retrying in {retry_delay} seconds...")
                                    time.sleep(retry_delay)
                                else:
                                    print(f"Failed to send message to {user.username} after {max_retries} attempts: {e}")
                        
                        if message_sent:
                            accounts_messaged += 1
                            print(f"Successfully messaged {user.username} (followers: {followers})")
                            
                            # Log the messaged account
                            new_entry = {
                                'username': user.username,
                                'keyword': keyword,
                                'followers': followers,
                                'message_template': account_data['message_template'],
                                'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            self.messaged_df = pd.concat([
                                self.messaged_df,
                                pd.DataFrame([new_entry])
                            ], ignore_index=True)
                            self.messaged_df.to_csv('messaged_accounts.csv', index=False)
                            
                            # Add longer delay after successful message
                            self.human_like_delay(5, 10)
                        
                except Exception as e:
                    print(f"Error processing user {user.username}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Search error: {e}")
            messagebox.showerror("Error", f"An error occurred while searching: {str(e)}")
            
        return accounts_messaged
    
    def start_messaging(self):
        keyword = self.keyword_var.get()
        num_accounts = self.num_accounts_var.get()
        
        if not keyword:
            messagebox.showwarning("Error", "Please enter a search keyword")
            return
        
        # Get active accounts
        active_accounts = self.acc_df[self.acc_df['active'] == True]
        
        if active_accounts.empty:
            messagebox.showerror("Error", "No active accounts available")
            return
        
        total_accounts_messaged = 0
        
        # Messaging logic
        for _, account in active_accounts.iterrows():
            try:
                if self.login_to_instagram(account['username'], account['password']):
                    accounts_messaged = self.search_and_message_accounts(
                        keyword, 
                        num_accounts, 
                        account
                    )
                    total_accounts_messaged += accounts_messaged
                    
                    # Logout after each account
                    self.client.logout()
                    
            except Exception as e:
                print(f"Error with account {account['username']}: {e}")
                messagebox.showerror("Error", f"Issue with account {account['username']}")
        
        messagebox.showinfo("Complete", f"Messaging completed. Attempted to message {total_accounts_messaged} accounts.")
    
    def open_account_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Manage Instagram Accounts")
        
        # Account list frame
        account_frame = ttk.Frame(settings_window)
        account_frame.pack(padx=10, pady=10)
        
        # Refresh account list function
        def refresh_account_list():
            for widget in account_frame.winfo_children():
                widget.destroy()
            
            for i, row in self.acc_df.iterrows():
                frame = ttk.Frame(account_frame)
                frame.pack(fill='x', pady=2)
                
                # Active checkbox
                active_var = tk.BooleanVar(value=row['active'])
                ttk.Checkbutton(frame, variable=active_var, 
                    command=lambda idx=i, var=active_var: self.toggle_account_active(idx, var)
                ).pack(side='left', padx=5)
                
                # Username label
                ttk.Label(frame, text=row['username'], width=20).pack(side='left', padx=5)
                
                # Edit button
                ttk.Button(frame, text="Edit", 
                    command=lambda idx=i: self.edit_account(idx, settings_window)
                ).pack(side='left', padx=5)
                
                # Delete button
                ttk.Button(frame, text="Delete", 
                    command=lambda idx=i: self.delete_account(idx)
                ).pack(side='left', padx=5)
        
        # Add account button
        ttk.Button(settings_window, text="Add New Account", 
            command=lambda: self.edit_account(None, settings_window)
        ).pack(pady=5)
        
        refresh_account_list()
    
    def toggle_account_active(self, index, var):
        self.acc_df.at[index, 'active'] = var.get()
        self.acc_df.to_csv('instagram_accounts.csv', index=False)
    
    def edit_account(self, index=None, parent_window=None):
        edit_window = tk.Toplevel(parent_window or self.root)
        edit_window.title("Add/Edit Account")
        
        # Create entry fields
        fields = [
            ("Username", "username"),
            ("Password", "password"),
            ("Message Template", "message_template"),
            ("Min Followers", "min_followers"),
            ("Max Followers", "max_followers")
        ]
        
        entries = {}
        for i, (label, field) in enumerate(fields):
            ttk.Label(edit_window, text=label).grid(row=i, column=0, padx=5, pady=2, sticky='w')
            entry = ttk.Entry(edit_window, width=40)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entries[field] = entry
        
        # Populate fields if editing existing account
        if index is not None:
            row = self.acc_df.iloc[index]
            for field, entry in entries.items():
                entry.insert(0, str(row[field]))
        
        # Active checkbox
        active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(edit_window, text="Active", variable=active_var).grid(row=len(fields), column=0, columnspan=2)
        
        def save_account():
            data = {field: entry.get() for field, entry in entries.items()}
            data['active'] = active_var.get()
            
            if index is not None:
                # Update existing account
                self.acc_df.iloc[index] = data
            else:
                # Add new account
                self.acc_df = pd.concat([
                    self.acc_df, 
                    pd.DataFrame([data])
                ], ignore_index=True)
            
            self.acc_df.to_csv('instagram_accounts.csv', index=False)
            edit_window.destroy()
            self.open_account_settings()
        
        ttk.Button(edit_window, text="Save", command=save_account).grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
    
    def delete_account(self, index):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this account?"):
            self.acc_df = self.acc_df.drop(index).reset_index(drop=True)
            self.acc_df.to_csv('instagram_accounts.csv', index=False)
            self.open_account_settings()
    
    def run(self):
        self.root.mainloop()

# Create and run the application
if __name__ == "__main__":
    messenger = InstagramMessenger()
    messenger.run() 