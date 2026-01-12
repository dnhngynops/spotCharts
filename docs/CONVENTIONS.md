# Project Conventions

Development and documentation guidelines for the Spotify Charts automation project.

---

## Documentation Policy

### Update, Don't Create
- **Always update existing documentation** rather than creating new standalone files
- Report findings and results in chat first
- Update relevant existing docs (README.md, CHANGELOG.md, SETUP.md, etc.)
- Keep documentation concise and integrated

### When Documenting Fixes/Changes:
1. Update `README.md` Recent Updates section with high-level summary
2. Add detailed entry to `docs/CHANGELOG.md` with version number
3. Add inline code comments with version tags (e.g., `# FIX (v1.2.0):`)
4. Update `docs/SETUP.md` Technical Notes if relevant
5. Report complete results in chat

### Test Results
- Capture output properly: `python script.py 2>&1 | tee output.log`
- Report results in chat with clear formatting
- Save data files to `/tmp/` for verification
- Document test methodology in CHANGELOG if significant

---

## Code Conventions

### Version Tags
When fixing bugs, add inline comments with version:
```python
# FIX (v1.2.0): Brief description
# Issue: Detailed explanation of problem
# Solution: How it's fixed
```

### Logging
- Use descriptive log messages for important milestones
- Include metrics in logs (counts, durations, etc.)
- Log both success and failure cases

---

## Testing Conventions

### Background Tasks
Always redirect output when running long-running tests:
```bash
python script.py 2>&1 | tee output.log
```

### Test Reporting
- Report pass/fail clearly with ✓/✗ symbols
- Include actual vs expected values
- Save test data to JSON for post-analysis
- Document any remaining issues

---

_Last updated: December 12, 2024_
