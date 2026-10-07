# Sample brief (simulated)
Client type: a state education agency (fictional, "Agency X").

Goal: replace a legacy mainframe-based licensing system with a cloud web portal where institutions submit applications, upload documents, pay fees and track status. Internal reviewers need a work queue, approvals and reports.

Functional needs
- Online application forms with save-and-resume and e-signature
- Document upload and checklist per application type
- Reviewer work queue, approval workflow and correspondence templates
- Integrations with a finance system (nightly), a student data system (nightly) and a payment provider (real time)
- Migration of about 20 years of records and scanned files

Known NFRs
- About 450 institutions and 60 internal users
- Peak load during a two-week filing window each year
- Data must stay in the United States
- Accessibility: WCAG 2.1 AA

Constraints
- Small delivery team, go-live in 12 months
- Existing identity provider must be used for sign-in
- Preferred cloud: open (Azure or AWS)

Not stated: availability target, RTO/RPO, retention period, audit logging scope, expected file volume.
