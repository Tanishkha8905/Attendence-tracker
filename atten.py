import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
import csv
from datetime import datetime, timedelta
import os

kivy.require('2.3.0')  # Specify the version of Kivy required


class AttendanceApp(App):
    def build(self):
        self.roll_range_input = TextInput(hint_text="Enter Roll Number Range (e.g., 1-50)", size_hint_y=None, height=30)

        # Create date dropdown for past 15 days and next 15 days
        self.date_spinner = Spinner(
            text="Select Date",
            values=self.generate_date_options(),
            size_hint_y=None,
            height=50
        )

        # Dropdown for subjects
        self.subject_spinner = Spinner(
            text="Select Subject",
            values=("Python", "ADS", "Java", "P&S", "UHV", "AI"),
            size_hint_y=None,
            height=50
        )

        self.start_button = Button(text="Start Attendance", size_hint_y=None, height=50)
        self.start_button.bind(on_press=self.start_attendance)

        self.save_button = Button(text="Save Attendance", size_hint_y=None, height=50)
        self.save_button.bind(on_press=self.save_attendance)
        self.save_button.disabled = True

        self.attendance_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.attendance_layout.bind(minimum_height=self.attendance_layout.setter('height'))

        self.scrollview = ScrollView()
        self.scrollview.add_widget(self.attendance_layout)

        self.main_layout = BoxLayout(orientation='vertical')
        self.main_layout.add_widget(self.roll_range_input)
        self.main_layout.add_widget(self.date_spinner)  # Add date dropdown
        self.main_layout.add_widget(self.subject_spinner)  # Add dropdown for subjects
        self.main_layout.add_widget(self.start_button)
        self.main_layout.add_widget(self.scrollview)
        self.main_layout.add_widget(self.save_button)

        return self.main_layout

    def generate_date_options(self):
        """Generate a list of date strings for the past 15 days and next 15 days."""
        today = datetime.today()
        date_range = [today + timedelta(days=i) for i in range(-15, 16)]
        return [date.strftime("%Y-%m-%d") for date in date_range]

    def start_attendance(self, instance):
        self.attendance_layout.clear_widgets()

        roll_range = self.roll_range_input.text.strip()
        date_str = self.date_spinner.text.strip()
        subject = self.subject_spinner.text

        # Validate roll range, date, and subject
        if not roll_range or date_str == "Select Date" or subject == "Select Subject":
            self.show_popup("Input Error", "Please enter valid roll number range, select a date, and choose a subject.")
            return

        try:
            start, end = map(int, roll_range.split('-'))
        except ValueError:
            self.show_popup("Input Error", "Invalid roll number range format.")
            return

        for roll in range(start, end + 1):
            row = BoxLayout(size_hint_y=None, height=30)
            label = Label(text=f"Roll {roll}", size_hint_x=None, width=200)
            checkbox = CheckBox(active=False, size_hint_x=None, width=50)
            row.add_widget(label)
            row.add_widget(checkbox)
            self.attendance_layout.add_widget(row)

        self.save_button.disabled = False

    def save_attendance(self, instance):
        directory = r"C:\Users\Admin\OneDrive\Desktop\Attendence\atten"
        if not os.path.exists(directory):
            os.makedirs(directory)

        date_str = self.date_spinner.text.strip()
        subject = self.subject_spinner.text

        if date_str == "Select Date":
            self.show_popup("Input Error", "Please select a valid date before saving.")
            return

        filename = os.path.join(directory, f"{subject}_attendance.csv")

        # Map roll numbers and attendance statuses
        attendance_data = {}
        for row in reversed(self.attendance_layout.children):
            label = row.children[1]  # Access label (roll number)
            checkbox = row.children[0]  # Access checkbox (attendance status)
            roll_number = label.text.split()[1]
            status = "Present" if checkbox.active else "Absent"
            attendance_data[int(roll_number)] = status

        attendance_data = dict(sorted(attendance_data.items()))

        headers = ["Roll Number"]
        data = {}

        if os.path.exists(filename):
            with open(filename, mode="r", newline="") as file:
                reader = list(csv.reader(file))
                headers = reader[0]
                data = {int(row[0]): row[1:] for row in reader[1:]}

            if date_str not in headers:
                headers.append(date_str)

            for roll, status in attendance_data.items():
                if roll in data:
                    # Update the attendance for the selected date
                    while len(data[roll]) < len(headers) - 1:  # Ensure alignment with headers
                        data[roll].append("Absent")
                    data[roll][-1] = status  # Update attendance for the current date
                else:
                    # Add a new roll number if it doesn't exist in the data
                    row = ["Absent"] * (len(headers) - 1)
                    row[-1] = status
                    data[roll] = row
        else:
            # New file: Initialize headers and data
            headers.append(date_str)
            for roll, status in attendance_data.items():
                data[roll] = [status]

        # Calculate attendance percentage
        if "Attendance Percentage" not in headers:
            headers.append("Attendance Percentage")

        for roll, attendance in data.items():
            total_days = len(headers) - 2
            present_count = attendance.count("Present")
            percentage = (present_count / total_days) * 100
            if len(attendance) < len(headers) - 1:
                attendance.append(f"{percentage:.2f}%")
            else:
                attendance[-1] = f"{percentage:.2f}%"

        # Write data back to CSV
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for roll, attendance in sorted(data.items()):
                writer.writerow([roll] + attendance)

        self.show_attendance_summary(filename, date_str)

    def show_attendance_summary(self, filename, date_str):
        """Display a summary of present and absent students for the selected date."""
        present_list = []
        absent_list = []

        with open(filename, mode="r", newline="") as file:
            reader = list(csv.reader(file))
            headers = reader[0]

            if date_str in headers:
                date_index = headers.index(date_str)
                for row in reader[1:]:
                    roll = row[0]
                    status = row[date_index]
                    if status == "Present":
                        present_list.append(roll)
                    elif status == "Absent":
                        absent_list.append(roll)

        # Prepare popup content
        summary = f"Date: {date_str}\nPresent: {', '.join(present_list)}\nAbsent: {', '.join(absent_list)}"
        self.show_popup("Attendance Summary", summary)

    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=10)
        popup_label = Label(text=message)
        popup_button = Button(text="Close", size_hint_y=None, height=50)
        popup_button.bind(on_press=lambda *args: popup.dismiss())
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(popup_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.6, 0.4))
        popup.open()


if __name__ == "__main__":
    AttendanceApp().run()