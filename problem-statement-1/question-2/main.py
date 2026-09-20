import requests
import matplotlib.pyplot as plt

API_URL = "https://msu-student-api.com/api/students"

response = requests.get(API_URL, timeout=10)
response.raise_for_status()

students = response.json()

if not students:
    raise ValueError("No student data returned by the API.")

names = [student["name"] for student in students]
scores = [student["score"] for student in students]

average = sum(scores) / len(scores)

print(f"Average Score: {average:.2f}")

plt.bar(names, scores)
plt.xlabel("Students")
plt.ylabel("Score")
plt.title("Student Test Scores")

plt.axhline(
    average,
    linestyle="--",
    label=f"Average = {average:.2f}"
)

plt.legend()
plt.tight_layout()
plt.show()