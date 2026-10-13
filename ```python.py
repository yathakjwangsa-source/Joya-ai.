
import ast
import json
import operator
import random
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ============================================================
# JOYA.AI 3.0
# Educational Assistant | Mathematics | AI | Space | Robotics
# ============================================================

BOT_NAME = "Joya.ai 3.0"

DATA_DIR = Path.home() / "JoyaAI"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NOTES_FILE = DATA_DIR / "notes.json"
HISTORY_FILE = DATA_DIR / "chat_history.json"
FLASHCARDS_FILE = DATA_DIR / "flashcards.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

OLLAMA_URL = "http://localhost:11434/api/chat"

# Change this to a model you have downloaded using Ollama.
OLLAMA_MODEL = "qwen3.5:4b"

# ============================================================
# SAFE ARITHMETIC CALCULATOR
# ============================================================

OPERATIONS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


def calculate(expression):
    """Evaluate basic arithmetic without using eval()."""

    if len(expression) > 200:
        raise ValueError("Expression is too long.")

    tree = ast.parse(expression, mode="eval")

    def solve(node, depth=0):
        if depth > 30:
            raise ValueError("Expression is too deeply nested.")

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.UnaryOp):
            operation = OPERATIONS.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operation.")

            return operation(solve(node.operand, depth + 1))

        if isinstance(node, ast.BinOp):
            operation = OPERATIONS.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operation.")

            left = solve(node.left, depth + 1)
            right = solve(node.right, depth + 1)

            if isinstance(node.op, ast.Pow):
                if abs(right) > 10 or abs(left) > 1_000_000:
                    raise ValueError("Exponent or base is too large.")

            if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if right == 0:
                    raise ZeroDivisionError("Division by zero is not allowed.")

            result = operation(left, right)

            if isinstance(result, complex):
                raise ValueError("Complex results are not supported.")

            if isinstance(result, float):
                if not __import__("math").isfinite(result):
                    raise ValueError("Result is outside the supported range.")

            if abs(result) > 10**100:
                raise ValueError("Result is too large.")

            return result

        raise ValueError("Enter a basic arithmetic expression.")

    return solve(tree.body)


def calculator():
    print("\n========== JOYA CALCULATOR ==========")
    print("Examples: 25 * 4, (10 + 5) / 3, 2 ** 5")
    print("Operators: +, -, *, /, //, %, **")

    expression = input("\nEnter calculation: ").strip()

    try:
        answer = calculate(expression)
        print("\nExpression:", expression)
        print("Answer:", answer)

    except (ValueError, SyntaxError, ZeroDivisionError,
            OverflowError, TypeError) as error:
        print("Calculator error:", error)


# ============================================================
# EDUCATIONAL KNOWLEDGE BASE
# ============================================================

LESSONS = {
    "python": (
        "Python is a programming language used in automation, "
        "software development, data science, robotics, and AI."
    ),

    "artificial intelligence": (
        "Artificial intelligence (AI) is a field of computer science "
        "that develops systems capable of tasks such as language "
        "processing, pattern recognition, and decision support."
    ),

    "machine learning": (
        "Machine learning is a branch of AI in which computers learn "
        "patterns from data to make predictions or decisions."
    ),

    "gravity": (
        "Gravity is the interaction that attracts objects with mass "
        "and shapes the motion of planets, stars, and galaxies. "
        "Near Earth's surface, objects accelerate downward at "
        "approximately 9.81 m/s²."
    ),

    "mars": (
        "Mars is the fourth planet from the Sun. It has a thin "
        "atmosphere made mostly of carbon dioxide, ancient river "
        "channels, polar ice, and evidence of a wetter past."
    ),

    "robotics": (
        "Robotics combines mechanical engineering, electronics, "
        "sensors, control systems, and programming to build machines "
        "that sense their surroundings and perform tasks."
    ),

    "satellites": (
        "Artificial satellites orbit Earth or other celestial bodies. "
        "They support navigation, communication, weather forecasting, "
        "scientific research, and Earth observation."
    ),

    "black holes": (
        "A black hole is a region of spacetime where gravity is so "
        "strong that nothing, including light, can escape from within "
        "its event horizon."
    ),

    "photosynthesis": (
        "Photosynthesis is the process through which plants use "
        "sunlight to convert carbon dioxide and water into sugars, "
        "releasing oxygen as a by-product."
    ),

    "newton's second law": (
        "Newton's second law states that net force equals mass "
        "multiplied by acceleration: F = ma. A 2 kg object with "
        "an acceleration of 3 m/s² experiences a net force of 6 N."
    ),

    "fractions": (
        "Fractions represent parts of a whole. For example, "
        "1/2 + 1/4 = 2/4 + 1/4 = 3/4."
    ),

    "climate change": (
        "Climate change refers to long-term changes in temperatures "
        "and weather patterns. Human greenhouse gas emissions are "
        "the main driver of current global warming."
    ),

    "data science": (
        "Data science combines statistics, programming, and domain "
        "knowledge to extract useful information from data."
    ),

    "computer vision": (
        "Computer vision enables computers to analyze images and "
        "videos. Applications include object detection, medical "
        "imaging, robotics, and satellite-image analysis."
    ),

    "neural networks": (
        "Neural networks are machine-learning models made of "
        "interconnected computational units. They can learn complex "
        "patterns from training data."
    ),

    "solar system": (
        "Our solar system contains the Sun, eight planets, dwarf "
        "planets, moons, asteroids, comets, and other objects "
        "bound by the Sun's gravity."
    ),

    "universe": (
        "The observable universe includes all space, time, matter, and "
        "energy that we can in principle observe. It is about 13.8 billion "
        "years old and is expanding. The observable universe is only the "
        "region whose light has had time to reach us; the full universe "
        "may be larger."
    ),

    "big bang": (
        "The Big Bang model describes the universe evolving from an "
        "extremely hot, dense early state about 13.8 billion years ago. "
        "It describes the expansion of space, not an explosion from one "
        "central point into empty space. Evidence includes cosmic "
        "expansion and the cosmic microwave background."
    ),

    "galaxies": (
        "A galaxy is a large system of stars, gas, dust, and dark matter "
        "held together by gravity. The Milky Way is our home galaxy, and "
        "it contains our Solar System."
    ),

    "stars": (
        "Stars are massive, luminous spheres of hot plasma held together "
        "by gravity. In their cores, nuclear fusion releases energy. The "
        "Sun is the closest star to Earth."
    ),

    "light-year": (
        "A light-year is a unit of distance, not time: it is how far light "
        "travels in one year in a vacuum, about 9.46 trillion kilometres. "
        "It helps describe the enormous distances between stars."
    ),

    "exoplanets": (
        "An exoplanet is a planet outside our Solar System that orbits "
        "another star, or in some cases a stellar remnant. Scientists "
        "often detect them by measuring a star's slight dimming or "
        "wobble."
    ),

    "cosmic microwave background": (
        "The cosmic microwave background (CMB) is faint radiation "
        "throughout space, released when the early universe became "
        "transparent about 380,000 years after the Big Bang. Its pattern "
        "is an important source of evidence about the early universe."
    ),

    "rocket science": (
        "Rocket propulsion produces thrust by expelling mass. "
        "Rocket performance depends on factors including propellant, "
        "exhaust velocity, mass ratio, and engine design."
    ),

    "global navigation satellite system": (
        "A Global Navigation Satellite System (GNSS) uses satellite "
        "signals to estimate a receiver's position, velocity, and time. "
        "GPS, Galileo, GLONASS, and NavIC are examples."
    ),

    "motion": (
        "Motion is a change in an object's position over time. Speed tells "
        "how quickly distance changes; velocity includes direction; "
        "acceleration describes how velocity changes."
    ),

    "force": (
        "A force is a push or pull that can change an object's motion. "
        "Newton's second law is F = ma: net force equals mass times "
        "acceleration, with force measured in newtons."
    ),

    "energy": (
        "Energy is the capacity to cause change or do work. Common forms "
        "include kinetic energy (motion), potential energy (stored), "
        "thermal, chemical, and electrical energy. Energy is conserved: "
        "it changes form rather than being created or destroyed."
    ),

    "atom": (
        "An atom is the smallest unit of an element that retains that "
        "element's chemical identity. It contains protons and neutrons "
        "in a nucleus, with electrons around the nucleus."
    ),

    "elements": (
        "A chemical element is a pure substance made of atoms with the "
        "same number of protons. The periodic table organizes elements "
        "by atomic number and recurring chemical properties."
    ),

    "compounds": (
        "A compound is a substance whose atoms of two or more different "
        "elements are chemically bonded in a fixed ratio. Water (H₂O) "
        "is made from hydrogen and oxygen."
    ),

    "chemical reactions": (
        "A chemical reaction rearranges atoms to form new substances. "
        "Atoms are conserved, so a balanced equation has the same number "
        "of each type of atom on both sides."
    ),

    "states of matter": (
        "The common states of matter are solid, liquid, and gas. They "
        "differ mainly in how particles move and are arranged; adding or "
        "removing energy can cause a change of state."
    ),

    "acids and bases": (
        "In water, acids increase hydrogen-ion concentration and bases "
        "reduce it or accept hydrogen ions. The pH scale describes "
        "acidity: below 7 is acidic, 7 is neutral, and above 7 is basic "
        "at ordinary conditions."
    ),

    "equations": (
        "An equation states that two expressions are equal. To solve for "
        "an unknown, perform the same valid operation on both sides until "
        "the variable is isolated, then substitute the answer to check it."
    ),

    "percentages": (
        "A percentage is a value out of 100. To find p percent of a "
        "quantity q, calculate (p / 100) × q. For example, 20% of 50 "
        "is 0.20 × 50 = 10."
    ),

    "geometry": (
        "Geometry studies shapes, sizes, angles, and positions. For "
        "example, the area of a rectangle is length × width, while the "
        "area of a triangle is (base × perpendicular height) / 2."
    ),

    "probability": (
        "Probability measures how likely an event is, from 0 (impossible) "
        "to 1 (certain). For equally likely outcomes, probability equals "
        "favorable outcomes divided by all possible outcomes."
    ),

    "continents": (
        "The seven-continent model names Africa, Antarctica, Asia, "
        "Europe, North America, South America, and Australia/Oceania. "
        "Some regions use different continent models because the "
        "boundaries are partly based on convention."
    ),

    "oceans": (
        "The five commonly recognized oceans are the Pacific, Atlantic, "
        "Indian, Southern, and Arctic. The Pacific is the largest, and "
        "the Southern Ocean surrounds Antarctica."
    ),

    "united nations": (
        "The United Nations (UN) is an international organization founded "
        "in 1945. Its work includes diplomacy, humanitarian assistance, "
        "human rights, and international cooperation. It has 193 member "
        "states; current decisions and leadership can change over time."
    ),

    "latitude and longitude": (
        "Latitude measures position north or south of the Equator; "
        "longitude measures position east or west of the Prime Meridian. "
        "Together they help describe locations on Earth."
    ),
}


def explain(topic):
    topic = topic.lower().strip()

    for key, explanation in LESSONS.items():
        if key in topic:
            return explanation

    return (
        "I don't have a prepared lesson for that topic yet. "
        "You can try a topic such as force, energy, atoms, equations, "
        "probability, continents, oceans, Python, or Mars. "
        "For broader questions, try chatting with Joya."
    )


def learning_center():
    print("\n========== LEARNING CENTER ==========")

    print("\nAvailable topics:")

    for index, topic in enumerate(LESSONS.keys(), start=1):
        print(f"{index}. {topic.title()}")

    topic = input("\nWhat would you like to learn? ").strip()

    if not topic:
        print("Please enter a topic.")
        return

    print("\nJoya.ai:", explain(topic))


# ============================================================
# QUIZ SYSTEM
# ============================================================

QUESTIONS = [
    {
        "question": "What is 7 * 8?",
        "options": ["A. 54", "B. 56", "C. 64", "D. 48"],
        "answer": "b",
        "explanation": "7 multiplied by 8 equals 56."
    },
    {
        "question": "Which planet is called the Red Planet?",
        "options": ["A. Venus", "B. Jupiter", "C. Mars", "D. Mercury"],
        "answer": "c",
        "explanation": "Mars appears reddish because of iron-rich minerals."
    },
    {
        "question": "What does CPU stand for?",
        "options": [
            "A. Central Processing Unit",
            "B. Computer Power Utility",
            "C. Central Program User",
            "D. Core Processing Utility"
        ],
        "answer": "a",
        "explanation": "CPU stands for Central Processing Unit."
    },
    {
        "question": "What is the chemical symbol for oxygen?",
        "options": ["A. Ox", "B. O", "C. Og", "D. Oy"],
        "answer": "b",
        "explanation": "The chemical symbol for oxygen is O."
    },
    {
        "question": "What is the formula for Newton's second law?",
        "options": ["A. E = mc²", "B. V = IR", "C. F = ma", "D. P = IV"],
        "answer": "c",
        "explanation": "Net force equals mass multiplied by acceleration."
    },
    {
        "question": "Which language is commonly used with AI libraries?",
        "options": ["A. Python", "B. HTML only", "C. CSS only", "D. None"],
        "answer": "a",
        "explanation": "Python is widely used for machine learning and AI."
    },
    {
        "question": "Which system provides satellite navigation?",
        "options": ["A. GNSS", "B. HDMI", "C. RAM", "D. USB"],
        "answer": "a",
        "explanation": "GNSS includes satellite navigation systems."
    },
]


def take_quiz():
    print("\n========== JOYA QUIZ ==========")

    try:
        count = int(input("How many questions? (1-7): "))
    except ValueError:
        print("Please enter a number.")
        return

    if not 1 <= count <= len(QUESTIONS):
        print(f"Choose a number between 1 and {len(QUESTIONS)}.")
        return

    selected = random.sample(QUESTIONS, count)
    score = 0

    for number, question in enumerate(selected, start=1):
        print(f"\nQuestion {number}: {question['question']}")

        for option in question["options"]:
            print(option)

        answer = input("Your answer (A/B/C/D): ").strip().lower()

        if answer == question["answer"]:
            print("Correct!")
            score += 1
        else:
            print("Not quite.")

        print("Explanation:", question["explanation"])

    percentage = score / count * 100

    print("\n========== RESULTS ==========")
    print(f"Score: {score}/{count}")
    print(f"Percentage: {percentage:.1f}%")

    if percentage == 100:
        print("Excellent! Perfect score.")
    elif percentage >= 70:
        print("Great work. Keep improving!")
    else:
        print("Keep practising. Every mistake is a chance to learn.")


# ============================================================
# NOTES SYSTEM
# ============================================================

def load_json(path, default):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
    except (OSError, json.JSONDecodeError):
        print(f"Warning: Could not read {path.name}.")

    return default


def save_json(path, data):
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except OSError as error:
        print("Could not save data:", error)


# ============================================================
# JEE PRACTICE, MOCK TESTS, AND AI QUESTION COACH
# ============================================================

JEE_QUESTIONS = [
    {
        "level": "main",
        "subject": "Physics",
        "question": (
            "A particle starts from rest and moves with constant "
            "acceleration 2 m/s² for 5 s. How far does it travel?"
        ),
        "options": ["A. 10 m", "B. 25 m", "C. 50 m", "D. 5 m"],
        "answer": "b",
        "explanation": (
            "Use s = ut + ½at². Here u = 0, a = 2 m/s², and t = 5 s, "
            "so s = 0 + ½ × 2 × 25 = 25 m."
        ),
    },
    {
        "level": "main",
        "subject": "Physics",
        "question": (
            "A 2 kg object moves at 3 m/s. What is its kinetic energy?"
        ),
        "options": ["A. 3 J", "B. 6 J", "C. 9 J", "D. 18 J"],
        "answer": "c",
        "explanation": (
            "Kinetic energy is K = ½mv². Substituting m = 2 kg and "
            "v = 3 m/s gives K = ½ × 2 × 9 = 9 J."
        ),
    },
    {
        "level": "main",
        "subject": "Chemistry",
        "question": (
            "How many moles of water are present in 18 g of H₂O? "
            "(Molar mass of H₂O = 18 g/mol.)"
        ),
        "options": ["A. 0.5 mol", "B. 1 mol", "C. 2 mol", "D. 18 mol"],
        "answer": "b",
        "explanation": (
            "Amount in moles = mass / molar mass = 18 g / "
            "(18 g/mol) = 1 mol."
        ),
    },
    {
        "level": "main",
        "subject": "Chemistry",
        "question": (
            "What amount of NaCl is in 5.85 g? "
            "(Molar mass of NaCl = 58.5 g/mol.)"
        ),
        "options": ["A. 0.01 mol", "B. 0.1 mol", "C. 1 mol", "D. 10 mol"],
        "answer": "b",
        "explanation": (
            "Moles = mass / molar mass = 5.85 / 58.5 = 0.10 mol."
        ),
    },
    {
        "level": "main",
        "subject": "Mathematics",
        "question": (
            "The roots of x² - 5x + 6 = 0 are:"
        ),
        "options": [
            "A. 2 and 3",
            "B. 1 and 6",
            "C. -2 and -3",
            "D. 0 and 5",
        ],
        "answer": "a",
        "explanation": (
            "Factor x² - 5x + 6 as (x - 2)(x - 3) = 0. Therefore "
            "the roots are x = 2 and x = 3."
        ),
    },
    {
        "level": "main",
        "subject": "Mathematics",
        "question": (
            "An arithmetic progression begins 3, 7, 11, ... . "
            "What is its 10th term?"
        ),
        "options": ["A. 35", "B. 39", "C. 40", "D. 43"],
        "answer": "b",
        "explanation": (
            "The first term is 3 and the common difference is 4. "
            "a₁₀ = 3 + (10 - 1) × 4 = 39."
        ),
    },
    {
        "level": "advanced",
        "subject": "Physics",
        "question": (
            "A block starts from rest and slides down a frictionless "
            "track through a vertical height of 5 m. Taking g = 10 m/s², "
            "what is its speed at the bottom?"
        ),
        "options": ["A. 5 m/s", "B. 10 m/s", "C. 25 m/s", "D. 50 m/s"],
        "answer": "b",
        "explanation": (
            "Conservation of mechanical energy gives mgh = ½mv². "
            "Thus v = √(2gh) = √(2 × 10 × 5) = 10 m/s. The mass cancels."
        ),
    },
    {
        "level": "advanced",
        "subject": "Physics",
        "question": (
            "Two 6 Ω resistors are connected in parallel across a 12 V "
            "ideal battery. What is the total current?"
        ),
        "options": ["A. 1 A", "B. 2 A", "C. 4 A", "D. 6 A"],
        "answer": "c",
        "explanation": (
            "For two equal resistors in parallel, R_eq = 6/2 = 3 Ω. "
            "Ohm's law gives I = V/R_eq = 12/3 = 4 A."
        ),
    },
    {
        "level": "advanced",
        "subject": "Chemistry",
        "question": (
            "A strong monoprotic acid is fully dissociated in water at "
            "25 °C and has concentration 1.0 × 10⁻³ mol/L. What is its pH?"
        ),
        "options": ["A. 2", "B. 3", "C. 7", "D. 11"],
        "answer": "b",
        "explanation": (
            "For a fully dissociated monoprotic acid, [H⁺] = 10⁻³ mol/L. "
            "pH = -log₁₀[H⁺] = 3."
        ),
    },
    {
        "level": "advanced",
        "subject": "Chemistry",
        "question": (
            "An element has isotopes of mass numbers 35 and 37 in the "
            "abundance ratio 3:1. What is its average atomic mass?"
        ),
        "options": ["A. 35.0 u", "B. 35.5 u", "C. 36.0 u", "D. 36.5 u"],
        "answer": "b",
        "explanation": (
            "Take the abundance-weighted mean: "
            "(3 × 35 + 1 × 37) / 4 = 142 / 4 = 35.5 u."
        ),
    },
    {
        "level": "advanced",
        "subject": "Mathematics",
        "question": (
            "For real x, what is the maximum value of f(x) = x(10 - x)?"
        ),
        "options": ["A. 10", "B. 20", "C. 25", "D. 100"],
        "answer": "c",
        "explanation": (
            "Complete the square: x(10 - x) = 25 - (x - 5)². "
            "Since a square is non-negative, the maximum is 25 at x = 5."
        ),
    },
    {
        "level": "advanced",
        "subject": "Mathematics",
        "question": (
            "A box has 5 red and 3 blue balls. Two balls are selected "
            "without replacement. What is the probability of getting "
            "one of each colour?"
        ),
        "options": ["A. 15/28", "B. 5/14", "C. 3/8", "D. 1/2"],
        "answer": "a",
        "explanation": (
            "Favourable pairs = 5 × 3 = 15. All pairs = C(8, 2) = 28. "
            "Therefore the probability is 15/28."
        ),
    },
]


def run_jee_test(selected, title):
    print(f"\n========== {title.upper()} ==========")
    print(
        "Practice format: single-correct questions, +4 for correct, "
        "-1 for incorrect, 0 for skipped. This is a learning exercise, "
        "not an official exam paper or complete current exam pattern."
    )
    print("Enter A, B, C, or D. Press Enter to skip a question.")

    responses = []
    for number, question in enumerate(selected, start=1):
        print(
            f"\nQuestion {number} [{question['subject']} | "
            f"{question['level'].title()}]:"
        )
        print(question["question"])
        for option in question["options"]:
            print(option)

        while True:
            answer = input("Your answer (A/B/C/D or Enter to skip): ").strip().lower()
            if answer in ("", "a", "b", "c", "d"):
                responses.append(answer)
                break
            print("Please enter A, B, C, D, or press Enter to skip.")

    correct = 0
    incorrect = 0
    skipped = 0
    score = 0

    print("\n========== ANSWERS AND EXPLANATIONS ==========")
    for number, (question, response) in enumerate(zip(selected, responses), start=1):
        if not response:
            skipped += 1
            result = "Skipped"
        elif response == question["answer"]:
            correct += 1
            score += 4
            result = "Correct (+4)"
        else:
            incorrect += 1
            score -= 1
            result = "Incorrect (-1)"

        print(f"\n{number}. {result}")
        print(f"Correct answer: {question['answer'].upper()}")
        print("Explanation:", question["explanation"])

    print("\n========== TEST SUMMARY ==========")
    print(f"Correct: {correct} | Incorrect: {incorrect} | Skipped: {skipped}")
    print(f"Practice score: {score}/{len(selected) * 4}")
    if correct == len(selected):
        print("Excellent work—your accuracy is strong. Try explaining one solution from memory.")
    elif correct > incorrect:
        print("Good progress. Review the explanations for missed questions, then try again.")
    else:
        print("Every attempt gives you useful feedback. Review one concept at a time and keep practising.")

    progress = load_json(PROGRESS_FILE, {})
    if not isinstance(progress, dict):
        progress = {}
    progress["jee_tests_completed"] = int(progress.get("jee_tests_completed", 0)) + 1
    progress["jee_questions_correct"] = (
        int(progress.get("jee_questions_correct", 0)) + correct
    )
    progress["jee_best_score"] = max(
        int(progress.get("jee_best_score", 0)),
        score,
    )
    save_json(PROGRESS_FILE, progress)


def jee_practice_menu():
    while True:
        print("\n========== JEE PRACTICE WITH JOYA ==========")
        print("1. JEE Main-style practice")
        print("2. JEE Advanced-style challenge")
        print("3. Mixed mock test (9 questions)")
        print("4. Ask Joya to solve my JEE question")
        print("5. Return to main menu")

        choice = input("Choose 1-5: ").strip()

        if choice == "1":
            questions = [q for q in JEE_QUESTIONS if q["level"] == "main"]
            run_jee_test(questions, "JEE Main-style practice")
        elif choice == "2":
            questions = [q for q in JEE_QUESTIONS if q["level"] == "advanced"]
            run_jee_test(questions, "JEE Advanced-style challenge")
        elif choice == "3":
            selected = []
            for subject in ("Physics", "Chemistry", "Mathematics"):
                subject_questions = [
                    q for q in JEE_QUESTIONS if q["subject"] == subject
                ]
                main_question = random.choice(
                    [q for q in subject_questions if q["level"] == "main"]
                )
                advanced_question = random.choice(
                    [q for q in subject_questions if q["level"] == "advanced"]
                )
                remaining = [
                    q for q in subject_questions
                    if q not in (main_question, advanced_question)
                ]
                selected.extend(
                    [main_question, advanced_question, random.choice(remaining)]
                )
            random.shuffle(selected)
            run_jee_test(selected, "Mixed JEE mock test")
        elif choice == "4":
            jee_question_coach()
        elif choice == "5":
            break
        else:
            print("Choose a number from 1 to 5.")


def jee_question_coach():
    print("\n========== JOYA JEE QUESTION COACH ==========")
    level_choice = input(
        "Choose level (1 = Main, 2 = Advanced, Enter = not sure): "
    ).strip()
    level = {
        "1": "JEE Main",
        "2": "JEE Advanced",
    }.get(level_choice, "JEE")
    subject = input("Subject (Physics, Chemistry, Mathematics, or blank): ").strip()
    question = input("Paste or type the complete question: ").strip()

    if not question:
        print("Please enter a question so Joya can help solve it.")
        return

    prompt = (
        f"Act as a patient {level} tutor"
        f"{f' for {subject}' if subject else ''}. Solve this learner's "
        "question carefully. Start by listing the given information and "
        "what is asked. Identify the relevant concept and formula, then "
        "show the derivation or calculation one step at a time. Explain "
        "why each step is valid, include units and assumptions, check the "
        "answer, and finish with the final answer, a common trap to avoid, "
        "and a short takeaway. If essential information is missing, ask "
        "one clear clarification question rather than inventing it.\n\n"
        f"Question:\n{question}"
    )
    print("\nJoya is working through the solution...")
    print("\nJoya:", ask_joya(prompt))


def explore_universe():
    topics = [
        "universe",
        "big bang",
        "galaxies",
        "stars",
        "black holes",
        "light-year",
        "exoplanets",
        "cosmic microwave background",
        "solar system",
    ]
    print("\n========== EXPLORE THE UNIVERSE ==========")
    for index, topic in enumerate(topics, start=1):
        print(f"{index}. {topic.title()}")
    print("0. Return to the main menu")

    choice = input("Choose a topic number: ").strip()
    if choice == "0":
        return
    try:
        topic_index = int(choice)
        if not 1 <= topic_index <= len(topics):
            raise ValueError
    except ValueError:
        print(f"Choose a number from 1 to {len(topics)}, or 0 to go back.")
        return

    topic = topics[topic_index - 1]
    print(f"\nJoya — {topic.title()}: {explain(topic)}")
    follow_up = input("\nWould you like to ask Joya a follow-up? (y/n): ").strip().lower()
    if follow_up in ("y", "yes"):
        question = input("What would you like to know? ").strip()
        if question:
            print("\nJoya:", ask_joya(
                f"Explain this follow-up question about {topic} clearly for a learner. "
                f"Show reasoning where useful and end with a short takeaway.\n\n{question}"
            ))


def notes_menu():
    while True:
        print("\n========== LEARNING NOTES ==========")
        print("1. Add a note")
        print("2. View notes")
        print("3. Delete a note")
        print("4. Return to main menu")

        choice = input("Choose 1-4: ").strip()

        notes = load_json(NOTES_FILE, [])

        if not isinstance(notes, list):
            notes = []

        if choice == "1":
            title = input("Note title: ").strip()
            content = input("Note content: ").strip()

            if title and content:
                notes.append({
                    "title": title,
                    "content": content,
                    "created_at": datetime.now().isoformat(
                        timespec="seconds"
                    )
                })

                save_json(NOTES_FILE, notes)
                print("Note saved successfully.")
            else:
                print("Title and content cannot be empty.")

        elif choice == "2":
            if not notes:
                print("No notes saved yet.")
                continue

            for index, note in enumerate(notes, start=1):
                print(f"\n{index}. {note['title']}")
                print(note["content"])
                print("Created:", note.get("created_at", "Unknown"))

        elif choice == "3":
            if not notes:
                print("No notes to delete.")
                continue

            for index, note in enumerate(notes, start=1):
                print(f"{index}. {note['title']}")

            try:
                index = int(input("Note number to delete: "))

                if 1 <= index <= len(notes):
                    removed = notes.pop(index - 1)
                    save_json(NOTES_FILE, notes)
                    print("Deleted:", removed["title"])
                else:
                    print("Invalid note number.")

            except ValueError:
                print("Please enter a valid number.")

        elif choice == "4":
            break

        else:
            print("Choose an option from 1 to 4.")


# ============================================================
# LOCAL AI INTEGRATION WITH OLLAMA
# ============================================================

JOYA_SYSTEM_PROMPT = (
    "You are Joya, a warm, respectful, globally minded educational "
    "assistant for learners. Answer questions about physics, chemistry, "
    "mathematics, general knowledge, and other subjects. Adapt explanations "
    "to the learner's level; define unfamiliar terms and use a simple "
    "example or analogy when useful. For a problem, identify what is given "
    "and what is asked, state assumptions when needed, choose a method, "
    "show each reasoning or calculation step, include units, and check the "
    "result when possible. For difficult problems, break the work into "
    "manageable steps and explain why each step is valid rather than "
    "skipping to the answer. If the question is ambiguous or lacks essential "
    "information, ask one concise clarifying question instead of guessing. "
    "For general knowledge, distinguish established facts from uncertainty "
    "and do not present changing or current facts as verified when you "
    "cannot check them. Structure substantial answers with clear headings "
    "such as Explanation, Steps, and Conclusion where appropriate. Finish "
    "with a concise conclusion or key takeaway and a genuine, brief "
    "encouragement; do not force these into trivial answers. Greet the "
    "learner naturally when appropriate, but do not repeat a greeting on "
    "every reply."
)


def build_joya_payload(prompt, stream=False):
    return {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": JOYA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": stream,
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 768,
        },
    }


def ask_joya(prompt):
    """Send a message to a locally running Ollama model."""

    payload = build_joya_payload(prompt)
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        message = result.get("message", {})
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            return "Joya received an empty answer. Please try asking in a simpler way."
        return content.strip()

    except urllib.error.HTTPError as error:
        if error.code == 404:
            return (
                f"Joya can't solve this yet because its AI model "
                f"'{OLLAMA_MODEL}' isn't installed. Open a terminal, run "
                f"`ollama pull {OLLAMA_MODEL}`, wait for it to finish, "
                "then try again."
            )

        return f"Joya couldn't complete the request (server error {error.code})."

    except urllib.error.URLError:
        return (
            "Joya couldn't connect to its AI service. Make sure the local "
            "AI service is running, then try again."
        )

    except (TimeoutError, OSError):
        return (
            "Joya's request timed out or could not be completed. "
            "Please try again."
        )

    except (json.JSONDecodeError, KeyError, TypeError):
        return "Joya received an unexpected response. Please try again."


def ai_chat(user_name=None):
    print("\n========== JOYA.AI CHAT ==========")
    hour = datetime.now().hour
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 18:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"

    name = f", {user_name}" if user_name else ""
    print(f"{time_greeting}{name}! I'm Joya, ready to help you learn.")
    print(
        "Ask about a concept, request a worked solution, or explore "
        "global general knowledge."
    )
    print(
        "For a useful answer, include the topic, your level, what you have "
        "tried, and where you got stuck (if relevant)."
    )
    print(
        "Example: “Explain Newton's second law for a beginner, then solve "
        "a simple example step by step.”"
    )
    print("Type 'back' to return to the menu.")

    while True:
        prompt = input("\nYou: ").strip()

        if prompt.lower() in ("back", "exit", "quit"):
            break

        if not prompt:
            print("Please enter a message.")
            continue

        print("\nJoya.ai is thinking...")

        response = ask_joya(prompt)

        print("\nJoya.ai:", response)

        history = load_json(HISTORY_FILE, [])

        if not isinstance(history, list):
            history = []

        history.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "user": prompt,
            "assistant": response
        })

        # Keep the most recent 200 exchanges.
        history = history[-200:]

        save_json(HISTORY_FILE, history)


def view_chat_history():
    history = load_json(HISTORY_FILE, [])

    print("\n========== CHAT HISTORY ==========")

    if not history:
        print("No conversations saved yet.")
        return

    for item in history[-20:]:
        print("\nTime:", item.get("time", "Unknown"))
        print("You:", item.get("user", ""))
        print("Joya.ai:", item.get("assistant", ""))


# ============================================================
# STUDY PLANNER + FLASHCARDS + PROGRESS
# ============================================================

def study_planner():
    print("\n========== STUDY PLANNER ==========")
    topic = input("What do you want to study? ").strip()

    if not topic:
        print("Please enter a topic.")
        return

    plan = [
        ("Day 1", "Learn the basic definition and key vocabulary."),
        ("Day 2", "Study the core concepts and important examples."),
        ("Day 3", "Practice 10 questions or 1 small exercise set."),
        ("Day 4", "Review mistakes and write a short summary."),
        ("Day 5", "Connect the topic to a real-world example or project."),
        ("Day 6", "Do timed practice and test recall without notes."),
        ("Day 7", "Revise, reflect, and make a 1-minute teaching summary."),
    ]

    print(f"\n7-day plan for: {topic.title()}\n")
    for day, focus in plan:
        print(f"{day}: {focus}")


def flashcards_menu():
    while True:
        print("\n========== FLASHCARDS ==========")
        print("1. Add a flashcard")
        print("2. Review flashcards")
        print("3. View all flashcards")
        print("4. Delete a flashcard")
        print("5. Return to main menu")

        choice = input("Choose 1-5: ").strip()
        cards = load_json(FLASHCARDS_FILE, [])

        if not isinstance(cards, list):
            cards = []

        if choice == "1":
            front = input("Front (question): ").strip()
            back = input("Back (answer): ").strip()

            if not front or not back:
                print("Front and back cannot be empty.")
                continue

            cards.append({
                "front": front,
                "back": back,
                "created_at": datetime.now().isoformat(timespec="seconds")
            })
            save_json(FLASHCARDS_FILE, cards)
            print("Flashcard added successfully.")

        elif choice == "2":
            if not cards:
                print("No flashcards available yet.")
                continue

            score = 0
            total = 0

            for card in cards:
                total += 1
                print(f"\nFront: {card['front']}")
                input("Press Enter to reveal the answer...")
                print(f"Back: {card['back']}")

                response = input("Did you answer it correctly? (y/n): ").strip().lower()
                if response in ("y", "yes"):
                    score += 1

            print(f"\nReview complete: {score}/{total} correct.")

            progress = load_json(PROGRESS_FILE, {"study_sessions": 0, "correct_answers": 0})
            progress["study_sessions"] = int(progress.get("study_sessions", 0)) + 1
            progress["correct_answers"] = int(progress.get("correct_answers", 0)) + score
            save_json(PROGRESS_FILE, progress)

        elif choice == "3":
            if not cards:
                print("No flashcards saved yet.")
                continue

            for index, card in enumerate(cards, start=1):
                print(f"\n{index}. Q: {card['front']}")
                print(f"   A: {card['back']}")

        elif choice == "4":
            if not cards:
                print("No flashcards to delete.")
                continue

            for index, card in enumerate(cards, start=1):
                print(f"{index}. {card['front']}")

            try:
                index = int(input("Flashcard number to delete: "))
                if 1 <= index <= len(cards):
                    removed = cards.pop(index - 1)
                    save_json(FLASHCARDS_FILE, cards)
                    print("Deleted:", removed["front"])
                else:
                    print("Invalid flashcard number.")
            except ValueError:
                print("Please enter a valid number.")

        elif choice == "5":
            break

        else:
            print("Choose a number from 1 to 5.")


def progress_dashboard():
    print("\n========== PROGRESS DASHBOARD ==========")

    notes = load_json(NOTES_FILE, [])
    cards = load_json(FLASHCARDS_FILE, [])
    history = load_json(HISTORY_FILE, [])
    progress = load_json(PROGRESS_FILE, {"study_sessions": 0, "correct_answers": 0})

    print(f"Notes saved: {len(notes) if isinstance(notes, list) else 0}")
    print(f"Flashcards saved: {len(cards) if isinstance(cards, list) else 0}")
    print(f"Chat exchanges saved: {len(history) if isinstance(history, list) else 0}")
    print(f"Study sessions completed: {progress.get('study_sessions', 0)}")
    print(f"Correct answers recorded: {progress.get('correct_answers', 0)}")
    print(f"JEE practice tests completed: {progress.get('jee_tests_completed', 0)}")
    print(f"JEE questions answered correctly: {progress.get('jee_questions_correct', 0)}")
    print(f"Best JEE practice score: {progress.get('jee_best_score', 0)}")


# ============================================================
# PERSONAL PROFILE
# ============================================================

def personal_profile(user_name):
    print("\n========== YOUR PROFILE ==========")

    if not user_name:
        print("No name set for this session.")
        user_name = input("What should Joya.ai call you? ").strip()

    if user_name:
        print(f"Welcome, {user_name}!")
        print("Your learning journey starts with curiosity and practice.")

    return user_name or None


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    user_name = None

    print("=" * 55)
    print("                 JOYA.AI 3.0")
    print(" Education | Mathematics | AI | Space | Robotics")
    print("=" * 55)

    print("\nWelcome to your personal learning assistant!")

    while True:
        print("\n============== MAIN MENU ==============")
        print("1. Learn a topic")
        print("2. Solve a maths problem")
        print("3. Take a quiz")
        print("4. Chat with Joya")
        print("5. Manage learning notes")
        print("6. View conversation history")
        print("7. Set or view your profile")
        print("8. Create a study plan")
        print("9. Manage flashcards")
        print("10. View progress dashboard")
        print("11. JEE practice and mock tests")
        print("12. Explore the Universe")
        print("13. Exit")

        choice = input("\nChoose an option (1-13): ").strip()

        try:
            if choice == "1":
                learning_center()

            elif choice == "2":
                calculator()

            elif choice == "3":
                take_quiz()

            elif choice == "4":
                ai_chat(user_name)

            elif choice == "5":
                notes_menu()

            elif choice == "6":
                view_chat_history()

            elif choice == "7":
                user_name = personal_profile(user_name)

            elif choice == "8":
                study_planner()

            elif choice == "9":
                flashcards_menu()

            elif choice == "10":
                progress_dashboard()

            elif choice == "11":
                jee_practice_menu()

            elif choice == "12":
                explore_universe()

            elif choice == "13":
                print("\nJoya.ai: Keep learning, building, and exploring!")
                print("Thank you for using Joya.ai 3.0.")
                break

            else:
                print("Please choose a number from 1 to 13.")

        except KeyboardInterrupt:
            print("\nOperation cancelled. Returning to the menu.")

        except Exception as error:
            print("An unexpected error occurred:", error)


if __name__ == "__main__":
    main()
