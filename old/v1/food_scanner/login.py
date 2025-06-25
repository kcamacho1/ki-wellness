from tkinter import *

def main_account_screen():

    main_screen = Tk() # Creates GUI window
    main_screen.geometry("350x250") # Set GUI cofigurations of window
    main_screen.title("Account Login") # Set the title of the GUI Window

# Create a From label
Label(text="Choose Login Or Register", bg="blue", width="300", height="2", font=("Calibri", 13)).pack()
Label(text="").pack()

# Create a register button
Button(text="Register", height="2", width="30").pack()

main_screen.mainloop() # Start the GUI

main_account_screen() # Call the main_account_screen() function
