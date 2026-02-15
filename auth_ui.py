import tkinter as tk
from tkinter import messagebox
from face_system import (
    create_account,
    login,
    verify_face,
    lock_door,
    get_full_name,
    update_face,
    delete_account
)

BG = "#5B4BDB"
CARD = "#FFFFFF"
GREEN = "#2ECC71"
RED = "#E74C3C"

root = tk.Tk()
root.title("Smart Door")
root.geometry("900x600")
root.configure(bg=BG)
root.resizable(False, False)

card = tk.Frame(root, bg=CARD, width=400, height=550)
card.place(relx=0.5, rely=0.5, anchor="center")
card.pack_propagate(False)

title = tk.Label(card, font=("Helvetica", 22, "bold"), bg=CARD)
title.pack(pady=30)

content = tk.Frame(card, bg=CARD)
content.pack()

current_user = None

def clear():
    for w in content.winfo_children():
        w.destroy()

def input_box(label, hide=False):
    tk.Label(content, text=label, bg=CARD).pack(anchor="w")
    e = tk.Entry(content, width=30, show="*" if hide else "")
    e.pack(ipady=6, pady=8)
    return e



def show_login():
    clear()
    title.config(text="Login", fg="black")

    username = input_box("Username")
    password = input_box("Password", hide=True)

    def do_login():
        global current_user
        if login(username.get(), password.get()):
            current_user = username.get()
            show_dashboard()
        else:
            messagebox.showerror("Denied", "Invalid credentials")

    tk.Button(content, text="Login",
              width=25, height=2,
              bg=BG, fg="black",
              command=do_login).pack(pady=20)

    tk.Button(content, text="Create Account",
              bg=CARD, fg=BG, bd=0,
              command=show_signup).pack()



def show_signup():
    clear()
    title.config(text="Create Account")

    first_name = input_box("First Name")
    last_name = input_box("Last Name")
    username = input_box("Username")
    password = input_box("Password", hide=True)

    def create():
        if not all([first_name.get(), last_name.get(),
                    username.get(), password.get()]):
            messagebox.showerror("Error", "All fields required")
            return

        create_account(
            username.get(),
            password.get(),
            first_name.get(),
            last_name.get()
        )

        messagebox.showinfo("Success", "Account created!")
        show_login()

    tk.Button(content, text="Register",
              width=25, height=2,
              bg=BG, fg="white",
              command=create).pack(pady=20)

    tk.Button(content, text="Back",
              bg=CARD, fg=BG, bd=0,
              command=show_login).pack()



def show_dashboard():
    clear()
    full_name = get_full_name(current_user)
    title.config(text=f"Welcome {full_name}")

    def unlock():
        if verify_face(current_user):
            messagebox.showinfo("Unlocked", "Door unlocked!")
        else:
            messagebox.showerror("Denied", "Face not recognized")

    def update():
        if update_face(current_user):
            messagebox.showinfo("Updated", "Face updated successfully!")

    def delete():
        confirm = messagebox.askyesno(
            "Delete Account",
            "Are you sure you want to delete your account?"
        )
        if confirm:
            if delete_account(current_user):
                messagebox.showinfo("Deleted", "Account deleted.")
                lock_door()
                show_login()

    tk.Button(content, text="Unlock Door",
              width=25, height=2,
              bg=GREEN, fg="black",
              command=unlock).pack(pady=15)

    tk.Button(content, text="Update Face",
              width=25, height=2,
              bg=BG, fg="black",
              command=update).pack(pady=10)

    tk.Button(content, text="Delete Account",
              width=25, height=2,
              bg=RED, fg="black",
              command=delete).pack(pady=10)

    tk.Button(content, text="Log Out",
              bg=CARD, fg=BG, bd=0,
              command=lambda: [lock_door(), show_login()]).pack(pady=20)


show_login()
root.mainloop()
