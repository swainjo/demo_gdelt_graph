# Project Workflow

## Guiding Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`
2. **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in `tech-stack.md` *before* implementation
3. **Clarity Over Cleverness:** Write clear, readable code that demonstrates concepts effectively
4. **Notebooks Must Run End-to-End:** All cells should execute without errors in sequential order
5. **Documentation is Essential:** Use markdown cells to explain what's happening and why

## Task Workflow

All tasks follow a strict lifecycle:

### Standard Task Workflow

1. **Select Task:** Choose the next available task from `plan.md` in sequential order

2. **Mark In Progress:** Before beginning work, edit `plan.md` and change the task from `[ ]` to `[~]`

3. **Implement the Task:**
   - Create or modify notebook cells to implement the functionality
   - Use markdown cells to explain concepts before code cells
   - Add inline comments for complex logic
   - Ensure code follows PEP 8 style guidelines

4. **Verify Notebook Runs:**
   - Run all cells in sequential order (Kernel → Restart & Run All)
   - Confirm all cells execute without errors
   - Verify output is clean and meaningful
   - Check that resources are cleaned up appropriately

5. **Document Deviations:** If implementation differs from tech stack:
   - **STOP** implementation
   - Update `tech-stack.md` with new design
   - Add dated note explaining the change
   - Resume implementation

6. **Commit Code Changes:**
   - Stage all code changes related to the task
   - Propose a clear, concise commit message e.g, `feat(bigquery): Add dataset creation example`
   - Perform the commit

7. **Attach Task Summary with Git Notes:**
   - **Step 7.1: Get Commit Hash:** Obtain the hash of the *just-completed commit* (`git log -1 --format="%H"`)
   - **Step 7.2: Draft Note Content:** Create a detailed summary for the completed task. This should include the task name, a summary of changes, a list of all created/modified files, and the core "why" for the change
   - **Step 7.3: Attach Note:** Use the `git notes` command to attach the summary to the commit:
     ```bash
     git notes add -m "<note content>" <commit_hash>
     ```

8. **Get and Record Task Commit SHA:**
   - **Step 8.1: Update Plan:** Read `plan.md`, find the line for the completed task, update its status from `[~]` to `[x]`, and append the first 7 characters of the *just-completed commit's* commit hash
   - **Step 8.2: Write Plan:** Write the updated content back to `plan.md`

9. **Commit Plan Update:**
   - **Action:** Stage the modified `plan.md` file
   - **Action:** Commit this change with a descriptive message (e.g., `conductor(plan): Mark task 'Add BigQuery dataset creation' as complete`)

### Phase Completion Verification and Checkpointing Protocol

**Trigger:** This protocol is executed immediately after a task is completed that also concludes a phase in `plan.md`.

1. **Announce Protocol Start:** Inform the user that the phase is complete and the verification and checkpointing protocol has begun.

2. **Run All Notebooks End-to-End:**
   - For each notebook modified in this phase, execute all cells in sequential order
   - Confirm all cells execute without errors
   - Verify outputs are clean, meaningful, and demonstrate the intended functionality

3. **Propose a Detailed, Actionable Manual Verification Plan:**
   - **CRITICAL:** To generate the plan, first analyze `product.md`, `product-guidelines.md`, and `plan.md` to determine the user-facing goals of the completed phase
   - You **must** generate a step-by-step plan that walks the user through the verification process, including any necessary commands and specific, expected outcomes
   - The plan you present to the user **must** follow this format:

     **For Notebook Changes:**
     ```
     All notebooks have been executed successfully. For manual verification, please follow these steps:

     **Manual Verification Steps:**
     1. **Open the notebook:** `gdelt_data_prep.ipynb`
     2. **Run all cells:** Kernel → Restart & Run All
     3. **Confirm that you see:** Clean execution with no errors, and the BigQuery dataset is created successfully
     4. **Verify:** Check your GCP console to confirm the dataset exists
     ```

4. **Await Explicit User Feedback:**
   - After presenting the detailed plan, ask the user for confirmation: "**Does this meet your expectations? Please confirm with yes or provide feedback on what needs to be changed.**"
   - **PAUSE** and await the user's response. Do not proceed without an explicit yes or confirmation.

5. **Create Checkpoint Commit:**
   - Stage all changes. If no changes occurred in this step, proceed with an empty commit.
   - Perform the commit with a clear and concise message (e.g., `conductor(checkpoint): Checkpoint end of Phase X`)

6. **Attach Auditable Verification Report using Git Notes:**
   - **Step 6.1: Draft Note Content:** Create a detailed verification report including the manual verification steps and the user's confirmation
   - **Step 6.2: Attach Note:** Use the `git notes` command and the full commit hash from the previous step to attach the full report to the checkpoint commit

7. **Get and Record Phase Checkpoint SHA:**
   - **Step 7.1: Get Commit Hash:** Obtain the hash of the *just-created checkpoint commit* (`git log -1 --format="%H"`)
   - **Step 7.2: Update Plan:** Read `plan.md`, find the heading for the completed phase, and append the first 7 characters of the commit hash in the format `[checkpoint: <sha>]`
   - **Step 7.3: Write Plan:** Write the updated content back to `plan.md`

8. **Commit Plan Update:**
   - **Action:** Stage the modified `plan.md` file
   - **Action:** Commit this change with a descriptive message following the format `conductor(plan): Mark phase '<PHASE NAME>' as complete`

9. **Announce Completion:** Inform the user that the phase is complete and the checkpoint has been created, with the detailed verification report attached as a git note

### Quality Gates

Before marking any task complete, verify:

- [ ] All notebook cells execute without errors in sequential order
- [ ] Code follows project's code style guidelines (as defined in `code_styleguides/`)
- [ ] Markdown documentation is clear and explains the "why"
- [ ] No hardcoded credentials or sensitive information
- [ ] Output is clean and meaningful
- [ ] Resources are cleaned up appropriately (to avoid costs)

## Development Commands

### Setup
```bash
# Install required Python packages
pip install -r requirements.txt

# Set up GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Running Notebooks
```bash
# Start Jupyter Notebook
jupyter notebook

# Or start JupyterLab
jupyter lab
```

### Before Committing
```bash
# Verify notebooks run cleanly
# In Jupyter: Kernel → Restart & Run All

# Check code style (optional)
black --check *.ipynb
```

## Self-Review Checklist

Before marking a task complete:

1. **Functionality**
   - Notebook demonstrates the intended concept clearly
   - Code executes without errors
   - Error messages are clear and helpful

2. **Code Quality**
   - Follows style guide (PEP 8)
   - Clear variable/function names
   - Appropriate inline comments for complex logic

3. **Documentation**
   - Markdown cells explain concepts before code
   - Each section has a clear purpose
   - "Why" is explained, not just "what"

4. **Security**
   - No hardcoded credentials
   - Uses environment variables or Secret Manager
   - Follows principle of least privilege

5. **Resource Management**
   - Test resources are cleaned up
   - Cost implications are noted
   - Unnecessary resources are deleted

## Commit Guidelines

### Message Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Maintenance tasks

### Examples
```bash
git commit -m "feat(auth): Add remember me functionality"
git commit -m "fix(posts): Correct excerpt generation for short posts"
git commit -m "test(comments): Add tests for emoji reaction limits"
git commit -m "style(mobile): Improve button touch targets"
```

## Definition of Done

A task is complete when:

1. Notebook implements the specified functionality
2. All cells execute without errors in sequential order
3. Markdown documentation is clear and comprehensive
4. Code follows style guidelines (PEP 8)
5. No hardcoded credentials or sensitive information
6. Output is clean and meaningful
7. Implementation notes added to `plan.md`
8. Changes committed with proper message
9. Git note with task summary attached to the commit

## Continuous Improvement

- Review notebooks periodically for clarity and accuracy
- Update based on user feedback and GCP service changes
- Document lessons learned
- Keep examples simple and focused
