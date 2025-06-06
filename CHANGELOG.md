# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of AWS DataZone MCP Server
- Complete AWS DataZone API coverage through MCP tools
- Modular architecture with dedicated tool modules
- Comprehensive error handling and logging
- Type safety with full type hints
- Professional documentation and contributing guidelines

### Tools Added
- **Domain Management**: `get_domain`, `create_domain`, `list_domain_units`, `create_domain_unit`, `add_entity_owner`, `add_policy_grant`, `search`
- **Project Management**: `create_project`, `get_project`, `list_projects`, `create_project_membership`, `list_project_profiles`, `create_project_profile`
- **Data Management**: `get_asset`, `create_asset`, `publish_asset`, `get_listing`, `search_listings`, `create_data_source`, `start_data_source_run`, `create_subscription_request`, `accept_subscription_request`, `get_subscription`, `get_form_type`, `list_form_types`, `create_form_type`
- **Glossary Management**: `create_glossary`, `create_glossary_term`, `get_glossary`, `get_glossary_term`
- **Environment Management**: `list_environments`, `create_connection`, `get_connection`, `list_connections`, `list_environment_blueprints`

## [0.1.0] - 2024-XX-XX

### Added
- Initial project structure
- Basic MCP server implementation
- Core DataZone API integrations
- Development environment setup
- Testing infrastructure
- Documentation framework

### Changed
- Renamed main server file from `datazone.py` to `server.py`
- Standardized type hints across all modules
- Improved error handling with specific AWS error codes

### Fixed
- Syntax warnings in docstrings
- Type hint consistency issues
- Missing boto3 dependency

### Security
- Implemented proper error handling to prevent information leakage
- Added input validation for all tool parameters 