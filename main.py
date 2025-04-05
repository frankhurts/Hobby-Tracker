# Install if needed
# let's see if I have everything setup for this, or if its going to break right away, knowing my luck
# pip install gspread oauth2client

# this is the Google Sheet API
import gspread

# it seems as tho a "Service Account" is going to act like a bot
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# Connect to your Google Sheet
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']

# Acquiring credentials through JSON (?)
# Q - am I going to have to add this json myself? Dont forget to remove it from the Github repo! 
creds = ServiceAccountCredentials.from_json_keyfile_name('your-credentials.json', scope)
client = gspread.authorize(creds)

# Connecting to the sheet
# Q - is this even the right name for the sheet?
sheet = client.open('Your Hobby Tracker').sheet1

# Read all hobbies
hobbies = sheet.get_all_records()

# Today's date
today = datetime.today().date()

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return today

# Define spaced repetition intervals based on Strength
def next_interval(strength):
    intervals = {
        1: 1,   # 1 day
        2: 3,   # 3 days
        3: 7,   # 7 days
        4: 14,  # 14 days
        5: 30   # 30 days
    }
    return intervals.get(strength, 7)

# Find hobbies due for review
# Q - is this creating a new list filled with due hobbies?
due_hobbies = [
    hobby for hobby in hobbies
    if hobby['Status'].lower() == 'active' and parse_date(hobby['Next Review Date']) <= today
]

# Sort by weakest strength first
due_hobbies.sort(key=lambda x: (x['Strength'], -x['Importance']))

if due_hobbies:
    print("🎯 Today's Recommended Hobbies to Review:")
    for idx, hobby in enumerate(due_hobbies[:3]):  # Suggest up to 3 hobbies
        print(f"{idx + 1}. {hobby['Hobby']} ({hobby['Subject']} > {hobby['Sub-category']}) [Strength: {hobby['Strength']}]")

    # Ask user which hobby they practiced
    choice = input("\nEnter the number of the hobby you practiced (or press Enter to skip): ")

    if choice:
        try:
            choice_idx = int(choice) - 1
            selected_hobby = due_hobbies[choice_idx]

            # Find row number (gspread rows start at 1, plus header row)
            all_hobbies = sheet.get_all_values()
            row_num = next(i+1 for i, row in enumerate(all_hobbies) if row[0] == selected_hobby['Hobby'])

            # Promote strength (+1), max 5
            new_strength = min(selected_hobby['Strength'] + 1, 5)

            # Set new next review date
            new_next_review = today + timedelta(days=next_interval(new_strength))

            # Update sheet
            sheet.update_cell(row_num, 10, new_strength)  # Column 10 = Strength
            sheet.update_cell(row_num, 5, new_next_review.strftime('%Y-%m-%d'))  # Column 5 = Next Review Date

            print(f"\n✅ Updated {selected_hobby['Hobby']}! New Strength: {new_strength}, Next Review: {new_next_review}")

        except Exception as e:
            print("❌ Error updating hobby:", e)

else:
    print("✅ No hobbies due for review today. You're on top of it!")
