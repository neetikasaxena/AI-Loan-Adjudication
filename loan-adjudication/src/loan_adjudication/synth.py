"""Synthetic applicant profiles and free-text narratives.

Profiles are sampled per *scenario* (clean approve, reject, review, mixed, threshold edge case) so the
label mix is controlled, but the ground-truth label always comes from running the rules engine.
Protected attributes (gender, ethnicity, region) are sampled independently of the financial profile
and only surface in the narrative through the name, pronouns and city, so they can be used for
fairness slicing and counterfactual tests.
"""

from __future__ import annotations

import copy
import random

from .schema import compute_dti

SCENARIOS = (("approve", 0.32), ("reject", 0.30), ("review", 0.18), ("reject_and_review", 0.08), ("edge", 0.12))
REJECT_VIOLATIONS = ("age", "credit", "income", "dti", "employment_status", "residency", "bankruptcy", "bank_account")
REVIEW_VIOLATIONS = ("tenure", "loan_amount", "missing")
EDGE_FIELDS = ("age", "credit", "income", "dti", "tenure", "loan_amount")
MISSABLE = ("credit_score", "dti", "bank_account", "tenure", "bankruptcy", "residency")
EMPLOYED = ("employed_full_time", "employed_part_time", "self_employed")

NAMES = {
    "White": {"female": ["Emily", "Sarah", "Megan", "Katie"], "male": ["Connor", "Jake", "Brad", "Matthew"],
              "last": ["Walsh", "Baker", "Sullivan", "Murphy"]},
    "Black": {"female": ["Lakisha", "Ebony", "Aaliyah", "Tamika"], "male": ["Darnell", "Jamal", "DeShawn", "Tyrone"],
              "last": ["Washington", "Jefferson", "Banks", "Booker"]},
    "Hispanic": {"female": ["Maria", "Lucia", "Ximena", "Guadalupe"], "male": ["Jose", "Alejandro", "Santiago", "Luis"],
                 "last": ["Hernandez", "Ramirez", "Gonzalez", "Flores"]},
    "Asian": {"female": ["Mei", "Priya", "Yuna", "Linh"], "male": ["Wei", "Arjun", "Hiroshi", "Minh"],
              "last": ["Nguyen", "Patel", "Kim", "Chen"]},
}
CITIES = {
    "Northeast": ["Boston", "Philadelphia", "Hartford"],
    "South": ["Atlanta", "Houston", "Memphis"],
    "Midwest": ["Chicago", "Columbus", "Omaha"],
    "West": ["Denver", "Phoenix", "Seattle"],
}
PRONOUNS = {
    "female": {"S": "She", "s": "she", "poss": "her", "Poss": "Her", "refl": "herself"},
    "male": {"S": "He", "s": "he", "poss": "his", "Poss": "His", "refl": "himself"},
}

NEUTRAL_PRONOUNS = {"S": "The applicant", "s": "the applicant", "poss": "their", "Poss": "Their", "refl": "themselves"}
# Used for training text so models cannot key on name, gender or location.
MASKED_IDENTITY = {"name": "[NAME]", "city": "[CITY]", "gender": "neutral"}
JOBS = ["nurse", "software developer", "teacher", "electrician", "warehouse supervisor", "accountant",
        "truck driver", "dental hygienist"]
BUSINESSES = ["landscaping", "catering", "photography", "cleaning", "consulting"]
LOAN_PURPOSES = ["debt consolidation", "a used car", "home repairs", "medical bills", "a wedding", "moving expenses"]

# Each entry is (first-person, third-person) template.
INTRO = [
    ("Hi, my name is {name} and I'm {age} years old, living in {city}.", "{name} is a {age}-year-old applicant from {city}."),
    ("My name is {name}, I am {age}, and I live in {city}.", "Applicant {name}, age {age}, lives in {city}."),
]
INTRO_NONRES = [
    ("Hi, my name is {name} and I'm {age} years old.", "{name} is a {age}-year-old applicant."),
]
EMPLOYMENT = {
    "employed_full_time": [("I work full-time as {job_a}.", "{S} works full-time as {job_a}."),
                           ("I have a full-time job as {job_a}.", "{S} has a full-time job as {job_a}.")],
    "employed_part_time": [("I work part-time as {job_a}.", "{S} works part-time as {job_a}."),
                           ("I have a part-time position as {job_a}.", "{S} has a part-time position as {job_a}.")],
    "self_employed": [("I'm self-employed and run my own {biz} business.", "{S} is self-employed and runs {poss} own {biz} business."),
                      ("I work for myself as a freelance {job}.", "{S} works for {refl} as a freelance {job}.")],
    "retired": [("I'm retired and live on my pension and savings.", "{S} is retired and lives on a pension and savings.")],
    "unemployed": [("I'm currently between jobs.", "{S} is currently unemployed."),
                   ("I was laid off recently and am looking for work.", "{S} was laid off recently and is looking for work.")],
    "student": [("I'm a full-time student.", "{S} is a full-time student.")],
}
TENURE = [
    ("I've been in this role for {dur}.", "{S} has been in {poss} current role for {dur}."),
    ("I've been with my current employer for {dur}.", "{S} has been with {poss} current employer for {dur}."),
]
TENURE_SELF = [("I've been running this work for {dur}.", "{S} has been running this work for {dur}.")]
INCOME_ANNUAL = [
    ("I earn {amt} a year before taxes.", "{S} earns {amt} per year gross."),
    ("My gross annual income is {amt}.", "{Poss} gross annual income is {amt}."),
]
INCOME_MONTHLY = [
    ("I bring in {amt} a month before taxes.", "{S} earns {amt} per month gross."),
    ("My gross monthly income is {amt}.", "{Poss} gross monthly income is {amt}."),
]
DTI_RATIO = [
    ("My debt-to-income ratio is {dti}%.", "{Poss} debt-to-income ratio is {dti}%."),
    ("My DTI is {dti}%.", "{Poss} DTI is {dti}%."),
]
DTI_DEBTS = [
    ("I pay {amt} a month toward credit cards and a car loan, not counting rent.",
     "{S} pays {amt} per month on existing debts, not counting rent."),
    ("My monthly debt payments, not including housing, come to {amt}.",
     "{Poss} monthly debt payments, not including housing, come to {amt}."),
]
CREDIT = [
    ("My credit score is {cs}.", "{Poss} FICO score is {cs}."),
    ("I have a FICO score of {cs}.", "{S} has a credit score of {cs}."),
]
CREDIT_DISTRACTOR = [
    ("My credit score used to be {old}, but it's {cs} now.", "{Poss} credit score was {old} a couple of years ago and is {cs} today."),
]
RESIDENCY = {
    "US_Citizen": [("I'm a U.S. citizen.", "{S} is a U.S. citizen."),
                   ("I was born in the US and am a citizen.", "{S} was born in the US and is a citizen.")],
    "Permanent_Resident": [("I'm a permanent resident with a green card.", "{S} is a lawful permanent resident."),
                           ("I have a green card.", "{S} holds a green card.")],
    "Visa_Holder": [("I'm here on an H-1B work visa.", "{S} is in the US on an H-1B visa."),
                    ("I'm in the country on a student visa.", "{S} is in the country on a student visa.")],
    "Non_Resident": [("I'm a non-resident and only in the US temporarily.", "{S} is not a US resident and is only in the country temporarily.")],
}
BANKRUPTCY = {
    "none": [("I've never filed for bankruptcy.", "{S} has never filed for bankruptcy."),
             ("There are no bankruptcies on my record.", "There are no bankruptcies on {poss} record.")],
    "recent": [("I filed for bankruptcy {y} ago.", "{S} filed for bankruptcy {y} ago."),
               ("I went through a Chapter 7 bankruptcy {y} ago.", "{S} went through a Chapter 7 bankruptcy {y} ago.")],
    "old": [("I had a bankruptcy {y} ago, but it was discharged long ago.", "{S} had a bankruptcy {y} ago; it has since been discharged.")],
}
BANK = {
    True: [("I have an active checking account with a local credit union.", "{S} has an active checking account."),
           ("I keep a savings and checking account at my bank.", "{S} keeps a savings and checking account at {poss} bank.")],
    False: [("I don't have a bank account right now; I mostly use cash.", "{S} does not currently have a bank account."),
            ("I closed my bank account last year and haven't opened a new one.", "{S} closed {poss} bank account last year and has not opened a new one.")],
}
LOAN = [
    ("I'd like to borrow {amt} for {purpose}.", "{S} is requesting {amt} for {purpose}."),
    ("I'm applying for a {amt} personal loan to cover {purpose}.", "{S} is applying for a {amt} personal loan to cover {purpose}."),
]
DISTRACTORS = [
    ("I have two kids and a dog.", "{S} has two kids and a dog."),
    ("I enjoy hiking on weekends.", "{S} enjoys hiking on weekends."),
    ("My rent is {rent} a month.", "{Poss} rent is {rent} a month."),
    ("I've been a customer of my bank for {n} years.", "{S} has been a customer of {poss} bank for {n} years."),
]
CLOSERS = [("Thanks for considering my application.", "Please advise on eligibility."), ("", "")]

# Held-out wordings: the LAST option of any family with 3+ options is used only for validation text.
HELDOUT_WORDINGS = [
    (INTRO, ("Hello, I'm {name}, a {age}-year-old from {city}.", "Meet {name}, {age} years old, based in {city}.")),
    (EMPLOYMENT["employed_full_time"], ("I'm employed full-time as {job_a}.", "{S} is employed full-time as {job_a}.")),
    (EMPLOYMENT["employed_part_time"], ("I'm employed part-time as {job_a}.", "{S} is employed part-time as {job_a}.")),
    (EMPLOYMENT["self_employed"], ("I own and operate a small {biz} company.", "{S} owns and operates a small {biz} company.")),
    (EMPLOYMENT["unemployed"], ("I'm out of work at the moment.", "{S} is out of work at the moment.")),
    (TENURE, ("I started this job {dur} ago.", "{S} started {poss} current job {dur} ago.")),
    (INCOME_ANNUAL, ("My salary is {amt} per year.", "{Poss} salary is {amt} per year.")),
    (INCOME_MONTHLY, ("I make {amt} monthly, before tax.", "{S} makes {amt} monthly, before tax.")),
    (DTI_RATIO, ("My debts take up {dti}% of my income.", "{Poss} debts take up {dti}% of {poss} income.")),
    (DTI_DEBTS, ("Between my car and cards I pay {amt} each month, rent excluded.",
                 "{S} spends {amt} a month servicing car and card debt, excluding rent.")),
    (CREDIT, ("My FICO comes in at {cs}.", "{Poss} FICO comes in at {cs}.")),
    (RESIDENCY["US_Citizen"], ("I hold U.S. citizenship.", "{S} holds U.S. citizenship.")),
    (RESIDENCY["Permanent_Resident"], ("I'm a lawful permanent resident.", "{S} is a lawful permanent resident of the US.")),
    (RESIDENCY["Visa_Holder"], ("I'm working here on a temporary work visa.", "{S} works here on a temporary work visa.")),
    (BANKRUPTCY["none"], ("I have no history of bankruptcy.", "{S} has no history of bankruptcy.")),
    (BANKRUPTCY["recent"], ("I declared bankruptcy {y} ago.", "{S} declared bankruptcy {y} ago.")),
    (BANK[True], ("My pay is deposited straight into my checking account.", "{Poss} pay is deposited into {poss} checking account.")),
    (BANK[False], ("I don't use a bank at the moment.", "{S} doesn't use a bank at the moment.")),
    (LOAN, ("I'm looking to finance {purpose} with a {amt} loan.", "{S} is seeking a {amt} loan for {purpose}.")),
]
for _family, _template in HELDOUT_WORDINGS:
    _family.append(_template)

def wording_pool(options: list, wording: str | None) -> list:
    """wording: None = all variants, 'train' = all but the last, 'val' = only the last (families of 3+)."""
    if wording is None or len(options) < 3:
        return options
    return options[-1:] if wording == "val" else options[:-1]

GREETINGS = [
    "Hi, thanks for reaching out about a personal loan. What can I help you with today?",
    "Hello! I can help you apply for a personal loan. How much would you like to borrow, and what is it for?",
]
QUESTIONS = {
    "employment": ["Are you currently working? If so, what do you do and how long have you been in that role?",
                   "Can you tell me about your current employment situation?"],
    "income": ["What is your gross income before taxes?",
               "How much do you earn before taxes, either per month or per year?"],
    "dti": ["What are your monthly debt payments, or your debt-to-income ratio if you know it?",
            "Do you know your debt-to-income ratio, or roughly how much you pay toward debts each month?"],
    "credit": ["What is your current credit score?", "Do you know your FICO credit score?"],
    "residency": ["What is your residency status in the US?", "Are you a U.S. citizen or permanent resident?"],
    "bankruptcy": ["Have you ever filed for bankruptcy? If so, when?", "Is there any bankruptcy in your history?"],
    "bank": ["Do you have an active bank account we can use for the funds?",
             "Do you currently have a checking or savings account?"],
    "tenure": ["How long have you been in your current role?", "And how long have you been doing that work?"],
}
MISSING_LABELS = {"credit": "credit score", "dti": "monthly debt payments", "residency": "residency status",
                  "bankruptcy": "bankruptcy history", "bank": "bank account details", "tenure": "time in your current role"}
DECLINES = ["I'd rather not share that.", "I'm not sure, sorry.", "I don't know that off the top of my head."]
FOLLOW_UPS = [
    "That's okay, but your {label} is part of our policy check. Could you share it?",
    "I understand. Without your {label} the application will need a manual review. Are you able to provide it?",
]
DECLINES_AGAIN = ["Sorry, I really can't say.", "I'd prefer not to say.", "I don't have that information right now."]
ACKS = ["Understood, I'll note that for the underwriter. ", "No problem, I'll flag that for review. "]
DIALOGUE_ORDER = ("employment", "income", "dti", "credit", "residency", "bankruptcy", "bank")

def _young(p: dict, rng: random.Random, age: int) -> None:
    p["age"] = age
    if p["employment_status"] == "retired":
        p["employment_status"] = rng.choice(["employed_part_time", "employed_full_time"])
    if p["tenure_months"] is not None:
        p["tenure_months"] = min(p["tenure_months"], rng.randint(6, 24))

def _make_employed(p: dict, rng: random.Random) -> None:
    if p["employment_status"] not in EMPLOYED:
        p["employment_status"] = "employed_full_time"

def _base_profile(rng: random.Random) -> dict:
    status = rng.choices(["employed_full_time", "employed_part_time", "self_employed", "retired"], [60, 10, 15, 15])[0]
    age = rng.randint(58, 80) if status == "retired" else rng.randint(21, 64)
    bankruptcy = "old" if rng.random() < 0.1 else "none"
    return {
        "age": age,
        "credit_score": rng.randint(680, 830),
        "annual_income_usd": rng.randrange(36000, 180001, 500),
        "dti": round(rng.uniform(5, 38), 1),
        "employment_status": status,
        "tenure_months": None if status == "retired" else rng.randint(7, min(240, (age - 18) * 12)),
        "residency_status": rng.choices(["US_Citizen", "Permanent_Resident"], [80, 20])[0],
        "bankruptcy": bankruptcy,
        "bankruptcy_years_ago": rng.randint(8, 15) if bankruptcy == "old" else None,
        "has_bank_account": True,
        "requested_amount_usd": None,
        "income_basis": None,
        "dti_basis": None,
        "missing": [],
        "loan_purpose": rng.choice(LOAN_PURPOSES),
        "old_credit_score": None,
    }

def _violate_reject(p: dict, kind: str, rng: random.Random) -> None:
    if kind == "age":
        _young(p, rng, rng.randint(16, 17))
    elif kind == "credit":
        p["credit_score"] = rng.randint(520, 669)
    elif kind == "income":
        p["annual_income_usd"] = rng.randrange(15000, 29500, 500)
    elif kind == "dti":
        p["dti"] = round(rng.uniform(40.5, 65), 1)
    elif kind == "employment_status":
        p["employment_status"] = rng.choice(["unemployed", "student"])
        p["tenure_months"] = None
    elif kind == "residency":
        p["residency_status"] = rng.choice(["Visa_Holder", "Non_Resident"])
    elif kind == "bankruptcy":
        p["bankruptcy"] = "recent"
        p["bankruptcy_years_ago"] = rng.randint(1, 6)
    elif kind == "bank_account":
        p["has_bank_account"] = False

def _violate_review(p: dict, kind: str, rng: random.Random) -> None:
    if kind == "tenure":
        _make_employed(p, rng)
        p["tenure_months"] = rng.randint(1, 5)
    elif kind == "loan_amount":
        p["requested_mult"] = rng.uniform(0.55, 1.2)
    elif kind == "missing":
        choice = rng.choice(MISSABLE)
        if choice == "tenure" and p["employment_status"] not in EMPLOYED:
            choice = "credit_score"
        if choice not in p["missing"]:
            p["missing"].append(choice)

def _edge(p: dict, kind: str, rng: random.Random) -> None:
    if kind == "age":
        _young(p, rng, rng.choice([17, 18]))
    elif kind == "credit":
        p["credit_score"] = rng.choice([669, 670, 671])
    elif kind == "income":
        p["annual_income_usd"] = rng.choice([29999, 30000, 30001])
        p["income_basis"] = "annual"
    elif kind == "dti":
        p["dti"] = rng.choice([39.9, 40.0, 40.1])
        p["dti_basis"] = "ratio"
    elif kind == "tenure":
        _make_employed(p, rng)
        p["tenure_months"] = rng.choice([5, 6, 7])
    elif kind == "loan_amount":
        p["requested_edge"] = rng.choice([-1, 0, 1])
        p["income_basis"] = "annual"

def _finalize(p: dict, rng: random.Random) -> None:
    if p["employment_status"] in EMPLOYED and p["tenure_months"] is None:
        p["tenure_months"] = rng.randint(7, 120)

    if p["income_basis"] is None:
        p["income_basis"] = "monthly" if rng.random() < 0.25 else "annual"
    if p["income_basis"] == "monthly":
        p["monthly_income_usd"] = round(p["annual_income_usd"] / 12)
        p["annual_income_usd"] = p["monthly_income_usd"] * 12
    income = p["annual_income_usd"]

    if p["dti_basis"] is None:
        p["dti_basis"] = "debts" if rng.random() < 0.3 else "ratio"
    if p["dti_basis"] == "debts":
        monthly_debt = round(p["dti"] / 100 * income / 12)
        if monthly_debt > 0:
            p["monthly_debt_usd"] = monthly_debt
            p["dti"] = compute_dti(monthly_debt, income)
        else:
            p["dti_basis"] = "ratio"

    half = income * 0.5
    if "requested_edge" in p:
        p["requested_amount_usd"] = int(half) + p.pop("requested_edge")
    elif "requested_mult" in p:
        amount = round(income * p.pop("requested_mult") / 500) * 500
        p["requested_amount_usd"] = max(amount, int(half) + 500)
    else:
        upper = max(1000, min(int(half), 50000))
        p["requested_amount_usd"] = rng.randrange(1000, upper + 1, 500)

    if "credit_score" not in p["missing"] and rng.random() < 0.1:
        p["old_credit_score"] = max(300, min(850, p["credit_score"] + rng.choice([-1, 1]) * rng.randint(40, 120)))

def sample_identity(rng: random.Random, exclude: dict | None = None) -> dict:
    genders = [g for g in PRONOUNS if not exclude or g != exclude["gender"]]
    groups = [e for e in NAMES if not exclude or e != exclude["ethnicity"]]
    regions = [r for r in CITIES if not exclude or r != exclude["region"]]
    gender, ethnicity, region = rng.choice(genders), rng.choice(groups), rng.choice(regions)
    first = rng.choice(NAMES[ethnicity][gender])
    last = rng.choice(NAMES[ethnicity]["last"])
    return {"name": f"{first} {last}", "gender": gender, "ethnicity": ethnicity, "region": region,
            "city": rng.choice(CITIES[region])}

def truth_application(p: dict) -> dict:
    miss = set(p["missing"])
    return {
        "applicant": {
            "age": p["age"],
            "credit_score": None if "credit_score" in miss else p["credit_score"],
            "annual_income_usd": float(p["annual_income_usd"]),
            "debt_to_income_ratio_percent": None if "dti" in miss else float(p["dti"]),
            "employment_status": p["employment_status"],
            "current_employment_duration_months": None if "tenure" in miss else p["tenure_months"],
            "residency_status": None if "residency" in miss else p["residency_status"],
            "has_bankruptcy_recent": None if "bankruptcy" in miss else p["bankruptcy"] == "recent",
            "has_verifiable_bank_account": None if "bank_account" in miss else p["has_bank_account"],
        },
        "loan_application": {"requested_amount_usd": float(p["requested_amount_usd"])},
    }

def _fmt_money(value: float, rng: random.Random) -> str:
    v = int(round(value))
    options = [f"${v:,}", f"{v:,} dollars"]
    if v >= 1000 and v % 1000 == 0:
        options.append(f"${v // 1000}k")
    elif v >= 1000 and v % 500 == 0:
        options.append(f"${v / 1000:.1f}k")
    return rng.choice(options)

def _fmt_duration(months: int, rng: random.Random) -> str:
    if months < 12 or rng.random() < 0.25:
        return f"{months} month{'s' if months != 1 else ''}"
    years, rem = divmod(months, 12)
    year_txt = f"{years} year{'s' if years != 1 else ''}"
    return year_txt if rem == 0 else f"{year_txt} and {rem} month{'s' if rem != 1 else ''}"

def _speaker(p: dict, identity: dict, rng: random.Random, first_person: bool, wording: str | None = None):
    pronouns = NEUTRAL_PRONOUNS if identity["gender"] == "neutral" else PRONOUNS[identity["gender"]]
    job = rng.choice(JOBS)
    ctx = {"name": identity["name"], "city": identity["city"], "age": p["age"], **pronouns,
           "job": job, "job_a": f"{'an' if job[0] in 'aeiou' else 'a'} {job}", "biz": rng.choice(BUSINESSES)}

    def say(options: list[tuple[str, str]], **extra) -> str:
        first, third = rng.choice(wording_pool(options, wording))
        return (first if first_person else third).format(**ctx, **extra)

    return say

def _fact_blocks(p: dict, say, rng: random.Random) -> dict[str, str | None]:
    """One sentence per fact; None = fact withheld. 'tenure' is absent when it does not apply."""
    miss = set(p["missing"])
    facts: dict[str, str | None] = {
        "intro": say(INTRO_NONRES if p["residency_status"] == "Non_Resident" else INTRO),
        "employment": say(EMPLOYMENT[p["employment_status"]]),
    }
    if p["tenure_months"] is not None:
        templates = TENURE_SELF if p["employment_status"] == "self_employed" else TENURE
        facts["tenure"] = None if "tenure" in miss else say(templates, dur=_fmt_duration(p["tenure_months"], rng))

    if p["income_basis"] == "monthly":
        facts["income"] = say(INCOME_MONTHLY, amt=_fmt_money(p["monthly_income_usd"], rng))
    else:
        facts["income"] = say(INCOME_ANNUAL, amt=_fmt_money(p["annual_income_usd"], rng))

    facts["dti"] = None
    if "dti" not in miss:
        if p["dti_basis"] == "debts":
            facts["dti"] = say(DTI_DEBTS, amt=_fmt_money(p["monthly_debt_usd"], rng))
        else:
            facts["dti"] = say(DTI_RATIO, dti=f"{p['dti']:g}")

    facts["credit"] = None
    if "credit_score" not in miss:
        if p["old_credit_score"] is not None:
            facts["credit"] = say(CREDIT_DISTRACTOR, cs=p["credit_score"], old=p["old_credit_score"])
        else:
            facts["credit"] = say(CREDIT, cs=p["credit_score"])

    facts["residency"] = None if "residency" in miss else say(RESIDENCY[p["residency_status"]])

    facts["bankruptcy"] = None
    if "bankruptcy" not in miss:
        years = p["bankruptcy_years_ago"]
        y = f"{years} year{'s' if years != 1 else ''}" if years else ""
        facts["bankruptcy"] = say(BANKRUPTCY[p["bankruptcy"]], y=y)

    facts["bank"] = None if "bank_account" in miss else say(BANK[p["has_bank_account"]])
    facts["loan"] = say(LOAN, amt=_fmt_money(p["requested_amount_usd"], rng), purpose=p["loan_purpose"])
    return facts

def render_narrative(p: dict, identity: dict, seed: int, wording: str | None = None) -> str:
    """Render a profile as free text. Same seed + different identity -> identical wording apart from identity."""
    rng = random.Random(seed)
    say = _speaker(p, identity, rng, first_person=rng.random() < 0.5, wording=wording)
    facts = _fact_blocks(p, say, rng)

    employment = " ".join(s for s in (facts["employment"], facts.get("tenure")) if s)
    blocks = [employment] + [facts[k] for k in ("income", "dti", "credit", "residency", "bankruptcy", "bank", "loan")
                             if facts[k]]
    intro = facts["intro"]

    rng.shuffle(blocks)

    distractors = wording_pool(DISTRACTORS, wording)
    for template in rng.sample(distractors, min(rng.choice([0, 1, 1, 2]), len(distractors))):
        distractor = say([template], rent=_fmt_money(rng.randrange(800, 2500, 50), rng), n=rng.randint(2, 12))
        blocks.insert(rng.randint(0, len(blocks)), distractor)

    closer = say(CLOSERS)
    return " ".join(part for part in [intro, *blocks, closer] if part)

def render_dialogue(p: dict, identity: dict, seed: int, wording: str | None = None) -> list[dict]:
    """Multi-turn intake chat (assistant asks, applicant answers). Ends on the applicant's last turn."""
    rng = random.Random(seed)
    facts = _fact_blocks(p, _speaker(p, identity, rng, first_person=True, wording=wording), rng)
    msgs = [{"role": "assistant", "content": rng.choice(GREETINGS)},
            {"role": "user", "content": f"{facts['intro']} {facts['loan']}"}]
    prefix = ""

    def ask(key: str) -> None:
        nonlocal prefix
        msgs.append({"role": "assistant", "content": prefix + rng.choice(QUESTIONS[key])})
        prefix = ""

    def withheld(key: str) -> None:
        nonlocal prefix
        msgs.append({"role": "user", "content": rng.choice(DECLINES)})
        msgs.append({"role": "assistant", "content": rng.choice(FOLLOW_UPS).format(label=MISSING_LABELS[key])})
        msgs.append({"role": "user", "content": rng.choice(DECLINES_AGAIN)})
        prefix = rng.choice(ACKS)

    for key in DIALOGUE_ORDER:
        ask(key)
        if key == "employment":
            msgs.append({"role": "user", "content": " ".join(s for s in (facts["employment"], facts.get("tenure")) if s)})
            if "tenure" in facts and facts["tenure"] is None:
                ask("tenure")
                withheld("tenure")
        elif facts[key] is None:
            withheld(key)
        else:
            msgs.append({"role": "user", "content": facts[key]})
    return msgs

def applicant_text(messages: list[dict]) -> str:
    return " ".join(m["content"] for m in messages if m["role"] == "user")

def generate_dataset(n: int, seed: int = 42, wording: str | None = None) -> list[dict]:
    rng = random.Random(seed)
    names, weights = zip(*SCENARIOS)
    records = []
    for i in range(n):
        scenario = rng.choices(names, weights)[0]
        p = _base_profile(rng)
        if scenario == "reject":
            for kind in rng.sample(REJECT_VIOLATIONS, k=rng.choices([1, 2], [70, 30])[0]):
                _violate_reject(p, kind, rng)
        elif scenario == "review":
            for kind in rng.sample(REVIEW_VIOLATIONS, k=rng.choices([1, 2], [75, 25])[0]):
                _violate_review(p, kind, rng)
        elif scenario == "reject_and_review":
            _violate_reject(p, rng.choice(REJECT_VIOLATIONS), rng)
            _violate_review(p, rng.choice(REVIEW_VIOLATIONS), rng)
        elif scenario == "edge":
            _edge(p, rng.choice(EDGE_FIELDS), rng)
        _finalize(p, rng)

        identity = sample_identity(rng)
        render_seed = rng.randrange(2**31)
        records.append({
            "application_id": f"APP-{i + 1:05d}",
            "scenario": scenario,
            "narrative": render_narrative(p, identity, render_seed, wording),
            "narrative_masked": render_narrative(p, MASKED_IDENTITY, render_seed, wording),
            "truth": truth_application(p),
            "identity": identity,
            "profile": copy.deepcopy(p),
            "render_seed": render_seed,
            "wording": wording,
        })
    return records

def rerender(record: dict, wording: str | None) -> dict:
    """Re-render a record's narratives with a given wording pool (used after the train/val split)."""
    p, seed = record["profile"], record["render_seed"]
    return {**record, "wording": wording,
            "narrative": render_narrative(p, record["identity"], seed, wording),
            "narrative_masked": render_narrative(p, MASKED_IDENTITY, seed, wording)}

def to_dialogue_record(record: dict, identity: dict | None = None) -> dict:
    """Same application as an intake chat; 'narrative' holds the applicant turns for the extractor."""
    wording, seed = record.get("wording"), record["render_seed"] + 1
    messages = render_dialogue(record["profile"], identity or record["identity"], seed, wording)
    masked = render_dialogue(record["profile"], MASKED_IDENTITY, seed, wording)
    out = {k: v for k, v in record.items() if k not in {"narrative", "narrative_masked"}}
    return {**out, "format": "dialogue", "messages": messages, "messages_masked": masked,
            "narrative": applicant_text(messages), "narrative_masked": applicant_text(masked)}

def counterfactual_narrative(record: dict, seed: int) -> tuple[str, dict]:
    """Re-render the same application with a different gender, ethnicity and region."""
    identity = sample_identity(random.Random(seed), exclude=record["identity"])
    if record.get("format") == "dialogue":
        return to_dialogue_record(record, identity)["narrative"], identity
    return render_narrative(record["profile"], identity, record["render_seed"], record.get("wording")), identity
