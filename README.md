# Zero-to-Intern: Practical Bug Hunt Assessments

Welcome to the **Zero-to-Intern Bug Hunt** repository.

This repository contains practical software engineering debugging challenges designed to evaluate and build your readiness for real-world engineering internships. 

Real engineering work rarely begins with a blank file or a simple algorithm puzzle. You will often work with unfamiliar codebases, investigate bug tickets reported by users, write automated tests, and explain your technical decisions.

---

## How It Works: The 5-Step Assessment Workflow

```mermaid
flowchart LR
    A["1. Fork & Clone"] --> B["2. Reproduce Bug"]
    B --> C["3. Implement Fix"]
    C --> D["4. Add Unit Tests"]
    D --> E["5. Submit for Review & AI Interview"]
```

1. **Fork this repository:** Click the **Fork** button at the top-right of this page to create your personal copy.
2. **Clone your fork locally:**
   ```bash
   git clone https://github.com/<your-username>/zero-to-intern-public.git
   cd zero-to-intern-public
   ```
3. **Navigate to your assigned task folder:** For example:
   ```bash
   cd level-1-beginner/task-4-grade-calculator
   ```
4. **Investigate & Reproduce:** Read the task `README.md` to understand the scenario and bug tickets. Run the visible tests:
   ```bash
   python3 -m unittest discover tests
   ```
   Observe the failing reproduction tests.
5. **Fix & Test:** Implement your solution in `src/`. Add new test cases to `tests/` covering edge cases.
6. **Fill out the Submission Form:** Complete the `CANDIDATE_SUBMISSION.md` file in your task folder.
7. **Push & Submit:** Push your commits to your fork and submit your repository link to your mentor for automated validation and scheduling your **Technical AI Defense Interview**.

---

## Level 1: Beginner Python Debugging Track

These foundational tasks focus on the core building blocks of Python. All tasks use the **Python 3 Standard Library only** (no external pip dependencies).

| Assessment ID | Task Name | Key Concept Tested | Est. Time | Folder Link |
|:---:|---|---|:---:|:---:|
| **BH-L1-004** | **EduGrade Grade Calculator** | Conditionals & Control Flow (`if` fallthrough vs `elif`) | 30–45m | [`level-1-beginner/task-4-grade-calculator`](./level-1-beginner/task-4-grade-calculator) |
| **BH-L1-005** | **QuickSplit Bill & Tip Calculator** | Arithmetic (`/` vs `//`) & String Type Coercion | 30–45m | [`level-1-beginner/task-5-bill-splitter`](./level-1-beginner/task-5-bill-splitter) |
| **BH-L1-002** | **UserAuth Profile Data Sanitizer** | String Immutability & Method Assignment (`.strip()`, `.lower()`, `.title()`) | 45–60m | [`level-1-beginner/task-2-user-sanitizer`](./level-1-beginner/task-2-user-sanitizer) |
| **BH-L1-003** | **WeatherStation Temperature Analyzer** | List Iteration, Sentinel Traps (`min=0.0`), Empty List Handling | 45–60m | [`level-1-beginner/task-3-temperature-tracker`](./level-1-beginner/task-3-temperature-tracker) |
| **BH-L1-001** | **TalentCart Order Pricing** | Lists of Dictionaries, Item Eligibility Filtering | 60–75m | [`level-1-beginner/task-1-cart-pricing`](./level-1-beginner/task-1-cart-pricing) |

---

## Assessment Rules & Evaluation

- **Environment:** Requires Python 3.8 or newer. Zero pip packages required.
- **Contract Integrity:** Do not change function signatures, module file names, or return dictionary keys.
- **Testing Discipline:** You must write new unit tests in `tests/` to prove your fix works across edge cases.
- **Responsible AI Use:** You are permitted to use AI coding tools (e.g., Copilot, ChatGPT, Claude), but you must disclose their use in `CANDIDATE_SUBMISSION.md` and thoroughly understand your code. During the follow-up AI interview, you will be asked to explain your implementation line by line.

---

## Standard Scoring Rubric (100 Points)

| Competency | Weight | What Reviewers Look For |
|---|:---:|---|
| **Bug Resolution & Correctness** | **30 pts** | Your code passes all automated evaluation tests and handles edge cases without side-effects. |
| **Root-Cause Analysis** | **20 pts** | You clearly articulate the technical cause of the defect, not just the symptom. |
| **Testing & Regression Prevention** | **20 pts** | You wrote comprehensive automated unit tests covering boundaries and potential regressions. |
| **Code Quality & Engineering Judgment** | **15 pts** | Clean, idiomatic, readable Python adhering to repository conventions. |
| **Responsible AI Use & Verification** | **15 pts** | You take full ownership of your code, explain all decisions, and critically verify any tool output. |
| **Total** | **100 pts** | |
