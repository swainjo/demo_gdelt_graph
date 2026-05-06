# Product Guidelines

## Documentation Style

### Clarity & Accessibility
- Write in clear, concise language suitable for intermediate technical audiences
- Define technical terms when first introduced
- Use active voice and present tense
- Break complex concepts into digestible steps
- Include visual aids (diagrams, screenshots) where helpful

### Notebook Structure
- Begin each notebook with a clear title and purpose statement
- Include a table of contents for notebooks with multiple sections
- Use markdown cells to explain concepts before code cells
- End with a summary and next steps or related resources

### Code Documentation
- Add inline comments for complex logic
- Use descriptive variable and function names
- Include docstrings for custom functions
- Explain why decisions were made, not just what the code does

## Technical Principles

### Security & Best Practices
- Never hardcode credentials or sensitive information
- Use environment variables or Secret Manager for secrets
- Follow principle of least privilege for IAM permissions
- Be mindful of costs when running demos (include notes about resource cleanup)
- Handle errors gracefully with clear error messages

### Code Quality
- Follow PEP 8 style guidelines for Python code for readability
- Keep code clear and easy to follow for demo purposes
- Use meaningful variable names that make the demo self-documenting
- Include error handling for API calls and data operations
- Clean up resources (close connections, delete test data) to avoid unnecessary costs

### Reproducibility
- Document prerequisites (GCP project setup, API enablement, permissions)
- Use parameterized variables for project IDs, datasets, and regions
- Include setup/teardown cells for test resources
- Notebooks should run cleanly end-to-end in a fresh environment
- Note any dependencies or configuration needed to run the demo

## User Experience

### Progressive Disclosure
- Start with simple examples before introducing complexity
- Build on previous concepts incrementally
- Offer both basic and advanced variations of operations
- Link to deep-dive resources for curious learners

### Practical Application
- Base examples on realistic use cases
- Include sample datasets that are relevant and interesting
- Show complete workflows, not just isolated operations
- Demonstrate troubleshooting common issues

### Helpful Context
- Explain when to use different approaches
- Include performance and cost considerations
- Link to official GCP documentation
- Provide troubleshooting tips for common errors

## Notebook Maintenance

- Update notebooks when GCP APIs or libraries change significantly
- Keep a changelog for significant updates
- Monitor GCP service updates and reflect changes as needed
