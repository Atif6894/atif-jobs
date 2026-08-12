import os
from dotenv import load_dotenv

load_dotenv()

# ── Adzuna ──────────────────────────────────────────────
ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_BASE    = "https://api.adzuna.com/v1/api/jobs/in/search"

# ── Remotive (no key needed) ─────────────────────────────
REMOTIVE_BASE  = "https://remotive.com/api/remote-jobs"

# ── Scheduler ────────────────────────────────────────────
REFRESH_INTERVAL_MINUTES = int(os.getenv("REFRESH_INTERVAL_MINUTES", 30))

# ── Resume Profile — Mohammed Atif ────────────────────────
# Weights: HIGH=3, MEDIUM=2, LOW=1
RESUME_KEYWORDS = {
    # HIGH match — core skills from resume
    "embedded":         3,
    "firmware":         3,
    "esp32":            3,
    "stm32":            3,
    "iot":              3,
    "mqtt":             3,
    "rtos":             3,
    "uart":             3,
    "spi":              3,
    "i2c":              3,
    "ble":              3,
    "embedded c":       3,
    "microcontroller":  3,
    "embedded systems": 3,
    "bare metal":       3,
    "wifi":             3,
    "wi-fi":            3,
    # MEDIUM match — related domains
    "hardware":         2,
    "pcb":              2,
    "robotics":         2,
    "autonomous":       2,
    "sensor":           2,
    "arduino":          2,
    "raspberry pi":     2,
    "can bus":          2,
    "telemetry":        2,
    "fpga":             2,
    "vlsi":             2,
    "rf":               2,
    "antenna":          2,
    "drone":            2,
    "embedded linux":   2,
    "ethernet":         2,
    "protocol":         2,
    "validation":       2,
    "bring-up":         2,
    # LOW match — broad ECE domain
    "electronics":      1,
    "communication":    1,
    "ece":              1,
    "electrical":       1,
    "testing":          1,
    "signal":           1,
    "circuit":          1,
    "semiconductor":    1,
    "telecom":          1,
    "networking":       1,
    "defence":          1,
    "aerospace":        1,
    "automotive":       1,
}

# Adzuna search queries (rotated across refreshes for variety)
ADZUNA_QUERIES = [
    "embedded firmware engineer",
    "embedded systems engineer",
    "iot engineer fresher",
    "hardware engineer fresher",
    "electronics engineer fresher",
    "firmware developer",
    "embedded developer",
    "robotics engineer fresher",
    "vlsi engineer fresher",
    "PCB design engineer",
    "hardware validation engineer",
    "RF engineer fresher",
    "embedded c developer",
    "microcontroller engineer",
    "electronics communication engineer",
]

# Remotive categories for remote ECE roles
REMOTIVE_CATEGORIES = [
    "software-dev",
    "hardware",
    "all-others",
]

# Negative keywords — filter out completely irrelevant roles
NEGATIVE_KEYWORDS = [
    "sales executive", "marketing manager", "business analyst", "hr manager",
    "recruiter", "accountant", "finance manager", "lawyer", "content writer",
    "graphic designer", "seo specialist", "digital marketing",
    "php developer", "ruby developer", "react developer",
    "angular developer", "node.js developer", "full stack developer",
    "frontend developer", "backend developer",
    "java developer", "python developer", "data analyst", "data scientist",
    "machine learning engineer", "devops engineer",
]

# Minimum match score to show a job (0–100)
MIN_MATCH_SCORE = 15

# Job categories for frontend filters
JOB_CATEGORIES = {
    "Firmware":  ["firmware", "embedded", "rtos", "microcontroller", "bare metal", "esp32", "stm32", "embedded c"],
    "IoT":       ["iot", "mqtt", "wifi", "ble", "telemetry", "raspberry pi", "arduino", "sensors"],
    "Robotics":  ["robotics", "autonomous", "drone", "ros", "servo", "motor control"],
    "Hardware":  ["hardware", "pcb", "validation", "bring-up", "signal integrity", "circuit"],
    "VLSI":      ["vlsi", "fpga", "asic", "verilog", "vhdl", "chip design", "semiconductor"],
    "Telecom":   ["telecom", "rf", "antenna", "networking", "protocol", "5g", "lte"],
    "Defence":   ["defence", "aerospace", "radar", "defense", "military"],
}
