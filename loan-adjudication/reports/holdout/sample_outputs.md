# Sample adjudications (validation set)

## HW-001 - scenario `handwritten` - truth `APPROVE` - predicted `FLAG_REVIEW`

> Hey there. 29 y/o full-time graphic designer here, been at the agency for 34 months. My salary is seventy-two thousand dollars. FICO 741 as of last week. Monthly obligations: student loan $310 + car $295. Citizen, born in Ohio. Clean record, no bankruptcy ever. Checking acct at a credit union. Looking for $9,500 to refinance a credit card.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
    {
      "id": "RULE-AGE-001",
      "name": "Minimum Age Requirement",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 18"
    },
    {
      "id": "RULE-INCOME-001",
      "name": "Minimum Annual Income",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least $30,000"
    },
    {
      "id": "RULE-DTI-001",
      "name": "Maximum Debt-to-Income Ratio (DTI)",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "no more than 40%"
    },
    {
      "id": "RULE-BANKRUPTCY-001",
      "name": "No Recent Bankruptcy Filing",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must not have filed for bankruptcy within the last 7 years."
    },
    {
      "id": "RULE-BANKACCTS-001",
      "name": "Verifiable Bank Account",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must possess at least one verifiable, active bank account for fund disbursement and repayment."
    },
    {
      "id": "RULE-EMPLOY-002",
      "name": "Minimum Employment Duration",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "at least 6 months"
    },
    {
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your age from the information provided; please submit documentation of it. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your bank account from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## HW-006 - scenario `handwritten` - truth `FLAG_REVIEW` - predicted `FLAG_REVIEW`

> 34, full-time warehouse lead for 2 yrs, $41,500/yr gross, credit 701, DTI 31%, US citizen, no bankruptcy, have a bank account. Want to borrow $26,000 for a car.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
    {
      "id": "RULE-AGE-001",
      "name": "Minimum Age Requirement",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 18"
    },
    {
      "id": "RULE-CREDIT-001",
      "name": "Minimum Credit Score",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 670"
    },
    {
      "id": "RULE-INCOME-001",
      "name": "Minimum Annual Income",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least $30,000"
    },
    {
      "id": "RULE-DTI-001",
      "name": "Maximum Debt-to-Income Ratio (DTI)",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "no more than 40%"
    },
    {
      "id": "RULE-BANKRUPTCY-001",
      "name": "No Recent Bankruptcy Filing",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must not have filed for bankruptcy within the last 7 years."
    },
    {
      "id": "RULE-BANKACCTS-001",
      "name": "Verifiable Bank Account",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must possess at least one verifiable, active bank account for fund disbursement and repayment."
    },
    {
      "id": "RULE-EMPLOY-002",
      "name": "Minimum Employment Duration",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "at least 6 months"
    },
    {
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "$26,000",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your age from the information provided; please submit documentation of it. We could not confirm your credit score from the information provided; please submit documentation of it. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your bank account from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## HW-003 - scenario `handwritten` - truth `REJECT` - predicted `FLAG_REVIEW`

> Applicant: 45-year-old self-employed electrician, business open 4 years. Personal income last year: $88,000. Score 655 per Experian. DTI 22%. Green card holder. No bankruptcies. Business and personal checking. Requesting $20k for equipment.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
    {
      "id": "RULE-CREDIT-001",
      "name": "Minimum Credit Score",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 670"
    },
    {
      "id": "RULE-DTI-001",
      "name": "Maximum Debt-to-Income Ratio (DTI)",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "no more than 40%"
    },
    {
      "id": "RULE-BANKACCTS-001",
      "name": "Verifiable Bank Account",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must possess at least one verifiable, active bank account for fund disbursement and repayment."
    },
    {
      "id": "RULE-EMPLOY-002",
      "name": "Minimum Employment Duration",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "at least 6 months"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your credit score from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bank account from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it."
}
```

## HW-002 - scenario `handwritten` - truth `APPROVE` - predicted `FLAG_REVIEW`

> I am writing on behalf of my father, who is 67 and retired from the postal service. His pension plus Social Security comes to $3,850 per month. Credit score: 702. He carries a 12% DTI. He's a naturalized U.S. citizen, has never declared bankruptcy, and banks with a local savings account. He needs $6,000 for a roof repair.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
    {
      "id": "RULE-AGE-001",
      "name": "Minimum Age Requirement",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 18"
    },
    {
      "id": "RULE-INCOME-001",
      "name": "Minimum Annual Income",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least $30,000"
    },
    {
      "id": "RULE-DTI-001",
      "name": "Maximum Debt-to-Income Ratio (DTI)",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "no more than 40%"
    },
    {
      "id": "RULE-BANKRUPTCY-001",
      "name": "No Recent Bankruptcy Filing",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must not have filed for bankruptcy within the last 7 years."
    },
    {
      "id": "RULE-BANKACCTS-001",
      "name": "Verifiable Bank Account",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must possess at least one verifiable, active bank account for fund disbursement and repayment."
    },
    {
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your age from the information provided; please submit documentation of it. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your bank account from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## HW-004 - scenario `handwritten` - truth `REJECT` - predicted `FLAG_REVIEW`

> I'm a 19 year old part-time barista (5 months in) making $2,100/month. My score is 690 and I put $500 a month toward a car payment. I'm a US citizen with a checking account and have never filed bankruptcy. I'd like $4,000 for a laptop and classes.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
    {
      "id": "RULE-CREDIT-001",
      "name": "Minimum Credit Score",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 670"
    },
    {
      "id": "RULE-INCOME-001",
      "name": "Minimum Annual Income",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least $30,000"
    },
    {
      "id": "RULE-DTI-001",
      "name": "Maximum Debt-to-Income Ratio (DTI)",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "no more than 40%"
    },
    {
      "id": "RULE-BANKRUPTCY-001",
      "name": "No Recent Bankruptcy Filing",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must not have filed for bankruptcy within the last 7 years."
    },
    {
      "id": "RULE-EMPLOY-002",
      "name": "Minimum Employment Duration",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "at least 6 months"
    },
    {
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your credit score from the information provided; please submit documentation of it. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## HW-005 - scenario `handwritten` - truth `REJECT` - predicted `FLAG_REVIEW`

> My name's Dana, 38. I've worked full time as a pharmacist for 10 years and make $128,000 annually. Credit score 780, debt-to-income 18 percent. I'm a permanent resident. I went through a bankruptcy four years ago after a medical emergency. I have a checking account. Requesting $25,000 to consolidate debt.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
    {
      "id": "RULE-AGE-001",
      "name": "Minimum Age Requirement",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 18"
    },
    {
      "id": "RULE-INCOME-001",
      "name": "Minimum Annual Income",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least $30,000"
    },
    {
      "id": "RULE-DTI-001",
      "name": "Maximum Debt-to-Income Ratio (DTI)",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "no more than 40%"
    },
    {
      "id": "RULE-BANKRUPTCY-001",
      "name": "No Recent Bankruptcy Filing",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must not have filed for bankruptcy within the last 7 years."
    },
    {
      "id": "RULE-EMPLOY-001",
      "name": "Current Employment Status",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "MAJOR",
      "your_value": "not provided",
      "requirement": "one of: employed full-time, employed part-time, self-employed, retired"
    },
    {
      "id": "RULE-EMPLOY-002",
      "name": "Minimum Employment Duration",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "at least 6 months"
    },
    {
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "$25,000",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your age from the information provided; please submit documentation of it. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your employment status from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## HW-010 - scenario `handwritten` - truth `APPROVE` - predicted `FLAG_REVIEW`

> Third-party note: applicant is 18 (turned 18 last month), full-time apprentice electrician for 6 months, earning $31,200 a year. FICO 670. DTI 40%. U.S. citizen, no bankruptcy history, has a checking account. Requesting $15,600.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
    {
      "id": "RULE-AGE-001",
      "name": "Minimum Age Requirement",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least 18"
    },
    {
      "id": "RULE-INCOME-001",
      "name": "Minimum Annual Income",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "at least $30,000"
    },
    {
      "id": "RULE-DTI-001",
      "name": "Maximum Debt-to-Income Ratio (DTI)",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "no more than 40%"
    },
    {
      "id": "RULE-BANKRUPTCY-001",
      "name": "No Recent Bankruptcy Filing",
      "status": "MISSING",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "not provided",
      "requirement": "Applicant must not have filed for bankruptcy within the last 7 years."
    },
    {
      "id": "RULE-EMPLOY-002",
      "name": "Minimum Employment Duration",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "at least 6 months"
    },
    {
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "$15,600",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your age from the information provided; please submit documentation of it. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```
