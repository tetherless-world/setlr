# Security Policy

## Supported Versions

The following versions of SETLr are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The SETLr team takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by email to:

**[mccusj@cs.rpi.edu](mailto:mccusj@cs.rpi.edu)**

Include the following information in your report:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Status Update**: We will send you regular updates about our progress within 7 days
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### What to Expect

After you submit a report, we will:

1. Confirm receipt of your vulnerability report
2. Investigate and validate the vulnerability
3. Work on a fix and determine a release timeline
4. Keep you informed of our progress
5. Credit you in the security advisory (if you wish)

### Disclosure Policy

- We ask that you do not publicly disclose the vulnerability until we have released a fix
- Once the vulnerability is fixed, we will publish a security advisory
- We will credit you as the reporter (unless you prefer to remain anonymous)

## Security Best Practices for Using SETLr

### Input Validation

When using SETLr to process data:

1. **Validate Input Sources**: Ensure data sources come from trusted origins
2. **Sanitize File Paths**: Be careful with user-provided file paths to prevent path traversal attacks
3. **Limit File Sizes**: Implement size limits for input files to prevent denial-of-service attacks
4. **Validate Templates**: Review JSLDT templates for potential code injection vulnerabilities

### Template Security

JSLDT templates use Jinja2 templating. To prevent template injection attacks:

1. **Avoid User-Provided Templates**: Do not allow untrusted users to provide arbitrary templates
2. **Use Autoescape**: Enable autoescaping when generating output formats that interpret special characters
3. **Limit Template Features**: Disable dangerous Jinja2 features if not needed
4. **Review Python Functions**: Carefully review any custom Python functions used in transforms

### RDF/SPARQL Security

When working with RDF data and SPARQL endpoints:

1. **Validate SPARQL Queries**: Sanitize any dynamic SPARQL queries to prevent SPARQL injection
2. **Authenticate Endpoints**: Use authentication for SPARQL Update endpoints
3. **Limit Endpoint Access**: Restrict network access to sensitive SPARQL endpoints
4. **Validate RDF Input**: Parse RDF data from untrusted sources with caution

### Python Security

When using SETLr's Python API:

1. **Pin Dependencies**: Use specific version numbers for production deployments
2. **Update Regularly**: Keep SETLr and its dependencies up to date
3. **Isolate Execution**: Run SETLr in isolated environments (containers, virtual machines)
4. **Limit Permissions**: Run with minimum required filesystem and network permissions

### XML Processing

When processing XML files:

1. **Prevent XXE Attacks**: SETLr uses lxml which has XXE protection enabled by default
2. **Limit Entity Expansion**: Be aware of XML bomb attacks with deeply nested entities
3. **Validate XML Sources**: Only process XML from trusted sources

## Security Features

### Built-in Protections

SETLr includes several security features:

- **Safe XML Parsing**: Uses lxml with secure defaults (XXE protection enabled)
- **Template Sandboxing**: Jinja2 templates run in a sandboxed environment
- **Input Validation**: Validates input formats and structures
- **Error Handling**: Provides detailed error messages without exposing sensitive information

## Known Limitations

- **Python Code Execution**: Custom Python transform functions execute with the permissions of the Python process
- **File System Access**: SETLr can read and write files based on the provided configuration
- **Network Access**: Can make HTTP requests and connect to SPARQL endpoints as configured

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.3) and announced through:

- GitHub Security Advisories
- Release notes in CHANGELOG.md
- GitHub Releases

Subscribe to repository notifications to stay informed about security updates.

## Questions?

If you have questions about security that are not sensitive in nature, please:

- Open a [GitHub Discussion](https://github.com/tetherless-world/setlr/discussions)
- Check the [documentation](docs/README.md)

For sensitive security matters, please email [mccusj@cs.rpi.edu](mailto:mccusj@cs.rpi.edu).

---

Thank you for helping keep SETLr and its users safe!
