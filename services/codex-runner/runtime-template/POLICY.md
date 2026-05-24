# Service Runtime Policy

Always blocked:

- Row data query or display
- Stored procedure execution
- Free SQL execution
- Business DB DDL/DML application
- Automatic create/alter/drop application
- Source apply or deploy
- Raw prompt persistence
- Raw provider response persistence
- Secret persistence
- General chatbot answers outside DB analysis scope

Allowed:

- Analyze sanitized metadata evidence
- Produce review-required artifact proposals
- Produce manual-review table design previews
- Produce Java/MyBatis draft files as proposals only

All outputs must include `productionReady: false` and review markers when uncertainty exists.
