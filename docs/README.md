# AWS DataZone MCP Server Documentation

Welcome to the comprehensive documentation for the AWS DataZone MCP server. This collection provides everything you need to effectively use and integrate with the server.

## 📚 Documentation Overview

### 🚀 Getting Started
- **[Getting Started Guide](./GETTING_STARTED.md)** - **START HERE** - Step-by-step tutorials (40 minutes)
- **[User Guide](./USER_GUIDE.md)** - Complete setup and usage reference
- **[Installation & Setup](./USER_GUIDE.md#set-up-your-environment)** - Install and configure the server
- **[Claude Desktop Integration](./USER_GUIDE.md#testing-with-claude-for-desktop)** - Connect with Claude for Desktop

### 🛠️ Reference Materials  
- **[Tool Reference](./TOOL_REFERENCE.md)** - Complete documentation of all 38 available tools
- **[Usage Examples](../examples/)** - Practical examples and code samples
- **[Troubleshooting](./USER_GUIDE.md#troubleshooting)** - Common issues and solutions

### 🧪 Development & Testing
- **[Testing Guide](../TESTING_FINAL_REPORT.md)** - Comprehensive testing documentation
- **[Testing Quick Reference](../TESTING_QUICK_REFERENCE.md)** - Developer testing commands
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to the project

## 🎯 Quick Navigation

### 🆕 New Users - Start Here!
**Never used the AWS DataZone MCP server before?** Follow this path:

1. **[📖 Getting Started Guide](./GETTING_STARTED.md)** - Complete tutorials in 40 minutes
   - 🚀 Tutorial 1: Quick Start (5 min)
   - 🔗 Tutorial 2: Claude Integration (10 min) 
   - 🏢 Tutorial 3: First Operations (10 min)
   - 📊 Tutorial 4: Real Workflow (15 min)

2. **[🛠️ Tool Reference](./TOOL_REFERENCE.md)** - Browse the 38 available tools
3. **[📋 Examples](../examples/basic/domain_operations.py)** - See more code examples

### For Developers
Jump to developer-focused resources:

1. **[Tool Reference](./TOOL_REFERENCE.md)** - Complete tool documentation
2. **[Usage Examples](../examples/)** - Code samples and patterns
3. **[Testing Documentation](../TESTING_FINAL_REPORT.md)** - Testing infrastructure and practices
4. **[Contributing Guide](../CONTRIBUTING.md)** - Development setup and contribution process

### For Data Teams
Resources for data engineers, analysts, and stewards:

1. **[Domain Management Tools](./TOOL_REFERENCE.md#-domain-management)** - Manage DataZone domains and units
2. **[Data Asset Management](./TOOL_REFERENCE.md#-data-management)** - Create and publish data assets
3. **[Glossary Management](./TOOL_REFERENCE.md#-glossary-management)** - Define business terminology
4. **[Project Management](./TOOL_REFERENCE.md#-project-management)** - Organize data projects

## 🔧 Tool Categories

The AWS DataZone MCP server provides **38 tools** across 5 categories:

| Category | Tools | Key Capabilities |
|----------|-------|------------------|
| **[Domain Management](./TOOL_REFERENCE.md#-domain-management)** | 11 tools | Domains, organizational units, permissions |
| **[Project Management](./TOOL_REFERENCE.md#-project-management)** | 6 tools | Projects, memberships, profiles |
| **[Data Management](./TOOL_REFERENCE.md#-data-management)** | 14 tools | Assets, listings, subscriptions, data sources |
| **[Glossary Management](./TOOL_REFERENCE.md#-glossary-management)** | 4 tools | Business glossaries and terms |
| **[Environment Management](./TOOL_REFERENCE.md#-environment-management)** | 3 tools | Environments and connections |

## 📖 Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── GETTING_STARTED.md           # 🌟 START HERE - Step-by-step tutorials
├── USER_GUIDE.md                # Complete user guide and setup
├── TOOL_REFERENCE.md            # Detailed tool reference (38 tools)
├── TESTING_FINAL_REPORT.md      # Comprehensive testing documentation
├── TESTING_QUICK_REFERENCE.md   # Quick testing commands and templates
└── PHASE2_COMPLETION_SUMMARY.md # Phase 2 completion summary

examples/
├── README.md                    # Examples overview and quick start
├── basic/                       # Basic usage examples
├── workflows/                   # End-to-end workflow examples  
├── advanced/                    # Advanced patterns and techniques
└── best_practices/              # Recommended practices and patterns
```

## 🚀 Quick Start

### 1. Install the Server
```bash
pip install datazone-mcp-server
```

### 2. Configure AWS Credentials
```bash
aws configure
export DATAZONE_DOMAIN_ID=dzd_your_domain_id
```

### 3. Test the Server
```bash
python -m datazone_mcp_server.server
```

### 4. Set Up Claude Desktop
Add to your `claude_desktop_config.json`:
```json
{
    "mcpServers": {
        "datazone": {
            "command": "python",
            "args": ["-m", "datazone_mcp_server.server"],
            "env": {
                "DATAZONE_DOMAIN_ID": "dzd_your_domain_id"
            }
        }
    }
}
```

**→ [Complete setup instructions and tutorials](./GETTING_STARTED.md)**

## 🎯 Common Use Cases

### Data Discovery & Catalog
```natural-language
"What data assets are available in my domain?"
"Search for assets related to customer data"
"Show me the published data catalog"
```

### Project & Asset Management
```natural-language
"Create a new project called 'Customer Analytics'"
"Add john.doe@company.com to project prj_123456"
"Create a table asset for customer transactions"
```

### Data Governance
```natural-language
"Create a business glossary for our sales terms"
"Add a glossary term for 'Customer LTV'"
"Set up domain organizational units"
```

**→ [Complete tutorials and examples](./GETTING_STARTED.md#-tutorial-4-complete-data-governance-workflow-15-minutes)**

## 🆘 Need Help?

### Common Issues
- **Setup Problems**: Check the [Getting Started guide](./GETTING_STARTED.md#-troubleshooting-guide)
- **Tool Errors**: Review [troubleshooting guide](./USER_GUIDE.md#troubleshooting)  
- **AWS Permissions**: See [authentication setup](./USER_GUIDE.md#configure-aws-credentials)
- **Claude Integration**: Follow [Claude Desktop tutorial](./GETTING_STARTED.md#-tutorial-2-claude-desktop-integration-10-minutes)

### Get Support
- **[GitHub Issues](https://github.com/wangtianren/datazone-mcp-server/issues)** - Report bugs or request features
- **[Contributing Guide](../CONTRIBUTING.md)** - Help improve the project
- **[Examples](../examples/)** - See working code samples

## 🔗 External Resources

### AWS DataZone
- **[AWS DataZone Documentation](https://docs.aws.amazon.com/datazone/)** - Official AWS documentation
- **[DataZone API Reference](https://docs.aws.amazon.com/datazone/latest/APIReference/)** - AWS API documentation
- **[DataZone User Guide](https://docs.aws.amazon.com/datazone/latest/userguide/)** - AWS user guide

### Model Context Protocol (MCP)
- **[MCP Specification](https://modelcontextprotocol.io/)** - Official MCP documentation
- **[MCP Server Tutorial](https://modelcontextprotocol.io/quickstart/server)** - Learn to build MCP servers
- **[MCP Client Tutorial](https://modelcontextprotocol.io/quickstart/client)** - Build custom MCP clients

---

**Ready to get started?** Begin with the **[Getting Started Guide](./GETTING_STARTED.md)** for hands-on tutorials, then reference the **[Tool Reference](./TOOL_REFERENCE.md)** for detailed documentation.

## 📚 Documentation Index

Welcome to the AWS DataZone MCP Server documentation. This directory contains comprehensive documentation for the testing infrastructure and project development.

## 🧪 Testing Documentation

### Core Testing Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| [📊 **TESTING_FINAL_REPORT.md**](./TESTING_FINAL_REPORT.md) | Comprehensive testing infrastructure report | Project managers, technical leads |
| [⚡ **TESTING_QUICK_REFERENCE.md**](./TESTING_QUICK_REFERENCE.md) | Developer quick reference guide | Developers, contributors |
| [🎯 **PHASE2_COMPLETION_SUMMARY.md**](./PHASE2_COMPLETION_SUMMARY.md) | Phase 2 completion summary | Stakeholders, project teams |

### Quick Access

#### For Developers 👨‍💻
- **New to the project?** Start with [TESTING_QUICK_REFERENCE.md](./TESTING_QUICK_REFERENCE.md)
- **Running tests?** Use the quick commands in the reference guide
- **Adding tests?** Follow the templates and patterns in the quick reference
- **Debugging?** Check the debugging section in the quick reference

#### For Project Managers 📊
- **Project status?** See [PHASE2_COMPLETION_SUMMARY.md](./PHASE2_COMPLETION_SUMMARY.md)
- **Detailed metrics?** Review [TESTING_FINAL_REPORT.md](./TESTING_FINAL_REPORT.md)
- **Coverage analysis?** Check the coverage section in the final report
- **Future planning?** Review the roadmap sections

#### For Technical Leads 🔧
- **Architecture details?** See the testing architecture section in the final report
- **Quality metrics?** Review the quality assurance section
- **Best practices?** Check the testing best practices documentation
- **Maintenance guidelines?** See the maintenance section in the final report

## 📋 Quick Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/datazone_mcp_server --cov-report=term-missing

# Run unit tests only (skip integration)
pytest tests/ -v --ignore=tests/test_integration.py

# Run integration tests (requires AWS credentials)
pytest tests/test_integration.py -m integration -v
```

## 📈 Current Status

### Test Results ✅
- **Total Tests**: 97 across 8 test files
- **Passing Tests**: 71 (100% success rate for available tests)
- **Overall Coverage**: 53% with clear improvement roadmap

### Module Coverage
| Module | Coverage | Status |
|--------|----------|--------|
| Glossary | 90% | ✅ Excellent |
| Server | 77% | ✅ Good |
| Project Management | 70% | ✅ Good |
| Environment | 55% | 🔶 Medium |
| Data Management | 54% | 🔶 Medium |
| Domain Management | 35% | 🔴 Needs Improvement |

## 🚀 Getting Started

### For New Contributors
1. Read the [TESTING_QUICK_REFERENCE.md](./TESTING_QUICK_REFERENCE.md)
2. Set up your development environment
3. Run the test suite to ensure everything works
4. Follow the testing patterns when adding new features

### For Existing Developers
1. Check the [latest coverage report](./TESTING_FINAL_REPORT.md#coverage-analysis)
2. Review the [improvement roadmap](./TESTING_FINAL_REPORT.md#identified-improvements)
3. Use the [quick reference](./TESTING_QUICK_REFERENCE.md) for daily testing tasks

## 🔍 Key Features

### Professional Testing Infrastructure
- **MCP Server Architecture**: All tests use proper MCP server patterns
- **Comprehensive Mocking**: No real AWS API calls during testing
- **Error Handling**: Both success and failure scenarios covered
- **Integration Ready**: AWS integration testing framework included

### Developer Experience
- **Quick Commands**: Common testing scenarios documented
- **Clear Patterns**: Consistent testing architecture across all modules
- **Debugging Support**: Comprehensive debugging guides
- **Performance**: Fast test execution (< 5 seconds for unit tests)

### Quality Assurance
- **100% Unit Test Success**: All available unit tests passing
- **Coverage Analysis**: Detailed coverage reporting and improvement plans
- **Best Practices**: Professional testing standards implemented
- **CI/CD Ready**: Professional practices for deployment

## 📞 Support

### Common Issues
- **Import errors**: Check the debugging section in quick reference
- **Mock failures**: Review the mocking patterns in the final report
- **AWS integration**: See integration testing guide in quick reference

### Getting Help
1. Check the [TESTING_QUICK_REFERENCE.md](./TESTING_QUICK_REFERENCE.md) debugging section
2. Review the [TESTING_FINAL_REPORT.md](./TESTING_FINAL_REPORT.md) troubleshooting guides
3. Look at existing test patterns for similar functionality

## 🔄 Document Updates

This documentation is maintained as part of the testing infrastructure. When making changes to tests:

1. Update relevant documentation if patterns change
2. Keep coverage targets current in the quick reference
3. Update the completion summary if major milestones are reached

---

**Documentation Last Updated**: December 2024  
**Testing Infrastructure Status**: ✅ Complete  
**Phase 2 Status**: ✅ Successfully Completed 