# DEMO — ambiguous folder (deliberate failure case)

This folder holds TWO release texts. The contract is one folder = one article, so `preflight` must
fail it and `scan` must flag it as ambiguous. Do not "fix" this fixture: it is the test that the
ambiguity is caught instead of silently reading the first file.

## Release A

Example A announced a fictional product on 1 March 2026. This paragraph exists only to be longer than
a few characters, so the file is a plausible release text for the checker.

## Release B

Example B announced a different fictional product on 2 March 2026. This paragraph exists for the same
reason, and the two files mean the folder cannot be consumed without a human decision.
