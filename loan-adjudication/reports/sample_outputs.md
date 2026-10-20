# Sample adjudications (validation set)

## APP-00004 - scenario `approve` - truth `APPROVE` - predicted `FLAG_REVIEW`

> Hello, I'm Hiroshi Patel, a 57-year-old from Denver. I'm looking to finance moving expenses with a 16,500 dollars loan. My salary is $90,000 per year. I'm a lawful permanent resident. I have no history of bankruptcy. I've been a customer of my bank for 7 years. Between my car and cards I pay $1,995 each month, rent excluded. My pay is deposited straight into my checking account. My FICO comes in at 760. I'm employed full-time as a nurse. I started this job 9 years ago.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
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
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## APP-00025 - scenario `review` - truth `FLAG_REVIEW` - predicted `FLAG_REVIEW`

> Hello, I'm Lakisha Washington, a 22-year-old from Columbus. I've been a customer of my bank for 2 years. My salary is $41,000 per year. I have no history of bankruptcy. I'm employed part-time as a nurse. I started this job 4 months ago. I hold U.S. citizenship. My debts take up 25.5% of my income. I'm looking to finance moving expenses with a $6,000 loan. My FICO comes in at 731. My pay is deposited straight into my checking account. Thanks for considering my application.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
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
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## APP-00006 - scenario `reject` - truth `REJECT` - predicted `REJECT`

> Hello, I'm Wei Kim, a 66-year-old from Philadelphia. I've been a customer of my bank for 4 years. I have no history of bankruptcy. I'm retired and live on my pension and savings. My FICO comes in at 561. My salary is 165,500 dollars per year. I'm a lawful permanent resident. I'm looking to finance home repairs with a 34,500 dollars loan. My pay is deposited straight into my checking account. My debts take up 49.7% of my income. Thanks for considering my application.

```json
{
  "decision": "REJECT",
  "failed_rules": [
    {
      "id": "RULE-CREDIT-001",
      "name": "Minimum Credit Score",
      "status": "FAIL",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "561",
      "requirement": "at least 670"
    }
  ],
  "missing_information": [
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
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "We are unable to approve your application at this time. Your credit score is 561, but the requirement is at least 670. Paying down balances and making on-time payments can raise your score; you may reapply once it reaches 670. Separately, these items would also need review: Minimum Annual Income; Maximum Debt-to-Income Ratio (DTI); No Recent Bankruptcy Filing; Loan Amount within Income Ratio."
}
```

## APP-00005 - scenario `approve` - truth `APPROVE` - predicted `FLAG_REVIEW`

> Meet Maria Gonzalez, 28 years old, based in Columbus. Her debts take up 24.7% of her income. Her salary is $144,000 per year. She is employed full-time as an electrician. She started her current job 4 years and 8 months ago. She is seeking a $1.5k loan for medical bills. She has been a customer of her bank for 9 years. She has no history of bankruptcy. Her FICO comes in at 720. Her pay is deposited into her checking account. She holds U.S. citizenship. Please advise on eligibility.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
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
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## APP-00009 - scenario `reject_and_review` - truth `REJECT` - predicted `REJECT`

> Hello, I'm Jamal Banks, a 27-year-old from Phoenix. I have no history of bankruptcy. My salary is 144,000 dollars per year. I hold U.S. citizenship. My FICO comes in at 535. I'm looking to finance moving expenses with a $147,500 loan. I'm employed full-time as a warehouse supervisor. I started this job 8 years and 4 months ago. My pay is deposited straight into my checking account. Between my car and cards I pay $2,232 each month, rent excluded. I've been a customer of my bank for 7 years.

```json
{
  "decision": "REJECT",
  "failed_rules": [
    {
      "id": "RULE-CREDIT-001",
      "name": "Minimum Credit Score",
      "status": "FAIL",
      "action_on_fail": "REJECT",
      "severity": "CRITICAL",
      "your_value": "535",
      "requirement": "at least 670"
    }
  ],
  "missing_information": [
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
  "reasoning": "We are unable to approve your application at this time. Your credit score is 535, but the requirement is at least 670. Paying down balances and making on-time payments can raise your score; you may reapply once it reaches 670. Separately, these items would also need review: Minimum Annual Income; Maximum Debt-to-Income Ratio (DTI); No Recent Bankruptcy Filing; Minimum Employment Duration; Loan Amount within Income Ratio."
}
```

## APP-00016 - scenario `approve` - truth `APPROVE` - predicted `FLAG_REVIEW`

> Meet Guadalupe Gonzalez, 27 years old, based in Chicago. She holds U.S. citizenship. Her pay is deposited into her checking account. She has no history of bankruptcy. Her debts take up 12.3% of her income. She is seeking a $26.5k loan for a used car. Her FICO comes in at 689. She owns and operates a small cleaning company. She has been running this work for 5 years and 5 months. She makes $13,000 monthly, before tax.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
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
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your employment status from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## APP-00019 - scenario `approve` - truth `APPROVE` - predicted `FLAG_REVIEW`

> Hello, I'm Brad Baker, a 59-year-old from Atlanta. My FICO comes in at 799. I own and operate a small cleaning company. I've been running this work for 5 years and 1 month. I have no history of bankruptcy. I'm looking to finance moving expenses with a $33,500 loan. My pay is deposited straight into my checking account. I hold U.S. citizenship. I've been a customer of my bank for 12 years. I make $12,417 monthly, before tax. Between my car and cards I pay $2,434 each month, rent excluded.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
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
      "id": "RULE-LOANAMT-001",
      "name": "Loan Amount within Income Ratio",
      "status": "MISSING",
      "action_on_fail": "FLAG_REVIEW",
      "severity": "MINOR",
      "your_value": "not provided",
      "requirement": "no more than not provided (50% of your annual income)"
    }
  ],
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your employment status from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```

## APP-00020 - scenario `approve` - truth `APPROVE` - predicted `FLAG_REVIEW`

> Meet Sarah Baker, 51 years old, based in Seattle. She is seeking a 16,500 dollars loan for moving expenses. She has no history of bankruptcy. Her FICO comes in at 698. She is employed full-time as a teacher. She started her current job 14 years ago. She has been a customer of her bank for 2 years. She holds U.S. citizenship. Her debts take up 18.7% of her income. Her pay is deposited into her checking account. Her salary is $152.5k per year.

```json
{
  "decision": "FLAG_REVIEW",
  "failed_rules": [],
  "missing_information": [
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
  "reasoning": "Your application needs a manual review by an underwriter before a final decision can be made. We could not confirm your annual income from the information provided; please submit documentation of it. We could not confirm your debt-to-income ratio from the information provided; please submit documentation of it. We could not confirm your bankruptcy history from the information provided; please submit documentation of it. We could not confirm your time in your current role from the information provided; please submit documentation of it. We could not confirm your requested loan amount from the information provided; please submit documentation of it."
}
```
