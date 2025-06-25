import csv
from datetime import datetime

# Ask user if they want to read or write to the food journal
openJournal = input("Do you want to 'read' or 'write' to your food journal? ").strip().lower()

# 📖 Read mode
if openJournal == "read":
    try:
        with open("meals.csv", mode='r') as file:
            csvFile = csv.reader(file)
            print("\n📋 Food Journal Entries:\n")
            for lines in csvFile:
                print(f"{lines[1]} on {lines[0]}")
    except FileNotFoundError:
        print("No journal found yet.")

# ✍️ Write mode
elif openJournal == "write":
    print("Enter each item you ate. Type 'exit' when you're done.\n")
    meal_entries = []

    while True:
        food = input("Food item: ").strip()
        if food.lower() == 'exit':
            break
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meal_entries.append([timestamp, food])

    if meal_entries:
        with open("meals.csv", mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(meal_entries)
        print("\n✅ Meal(s) saved to journal.")
    else:
        print("No meals entered.")

# ❌ Invalid input
else:
    print("ERROR: Only enter either 'read' or 'write'.")
