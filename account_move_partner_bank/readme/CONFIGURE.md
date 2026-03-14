To set up a bank account for a partner:

- Go to the partner record.
- Under the Invoicing/Accounting tab, set the Recipient Bank field.
  If the partner has a company set, you can only select a bank account
  linked to that company’s partner. If the partner has no company set,
  you can only select a bank account linked to the current company’s
  partner. This is a company-dependent field.

To set up a bank account for a sales team:

- Go to Sales > Configuration > Sales Teams.
- Select a team and set the Recipient Bank field. You can only choose a bank account
  linked to the company's partner (i.e., one of the company’s own bank accounts).

To use bank accounts in invoices:

- Go to Settings → Companies.
- Open a company record.
- In the Bank Account Sources tab, create one or more records.
  - Source Model: Select the model from which the bank field path is resolved
    (e.g., Account Move).
  - Bank Field Path: Enter the dot-path from the source model
    to a bank account (res.partner.bank), for example
    partner_id.bank_account_id or team_id.bank_account_id.

The bank account from the record with the highest priority (lowest sequence number) will be used first
when assigning the bank on invoices. If no value is found, the system proceeds to the next record, and so on.
