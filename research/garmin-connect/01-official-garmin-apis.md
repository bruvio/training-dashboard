# Official Garmin Connect APIs

## Overview

Garmin provides official developer APIs through their Connect Developer Program, which is free to approved business developers. The APIs offer structured access to health and fitness data from Garmin devices.

## Developer Programs

### 1. Garmin Connect Developer Program
- **Access**: Free to approved business developers
- **Application Process**: Applications are confirmed within 2 business days
- **Integration Time**: Typical integration takes 1-4 weeks
- **Evaluation Environment**: Provided for testing before production

### 2. Connect IQ SDK
- **Purpose**: For developing custom apps and watch faces
- **Latest Version**: Connect IQ 8.2.1 SDK (as of 2024-2025)
- **Features**: 16MB extended code space, native watch face editor support
- **Documentation**: Available at `developer.garmin.com/connect-iq/`

## Available APIs

### Activity API
- **Architecture**: REST-based for easy integration
- **Data Access**: FIT files containing detailed activity data
- **File Formats**: .FIT, .GPX, .TCX
- **Activity Types**: Running, cycling, swimming, yoga, strength training
- **Integration Options**: Ping/Pull or Push architecture

### Health API
- **Data Format**: JSON
- **Metrics Available**:
  - Steps and intensity minutes
  - Heart rate data
  - Sleep metrics
  - Calories burned
  - Stress levels
  - Pulse oximetry (SpO2)
  - Body Battery energy monitoring
  - Body composition
  - Respiration rate
  - Blood pressure

### Additional APIs
- **Women's Health API**: Menstrual cycle and pregnancy tracking
- **Training API**: Training plans and workout data
- **Courses API**: Route and course information

## Authentication

### OAuth 1.0a Implementation
- **Protocol**: OAuth 1.0a (NOT OAuth 2.0)
- **No OAuth 2.0 Plans**: Garmin has confirmed no plans to implement OAuth 2.0
- **Authentication Flow**:
  1. Acquire unauthorized request token
  2. Obtain user authorization via Garmin Connect
  3. Exchange authorized request token for user access token

### Requirements
- Consumer key and secret provided after approval
- User must consent and sync device data
- OAuth tokens valid for extended periods

## Data Availability

### Data Sources
- Data becomes available after users sync devices with Garmin Connect
- Requires initial user consent for data sharing
- Comprehensive device compatibility across Garmin ecosystem

### Customization Options
- Customizable data feeds
- Multi-project configurations supported
- Ability to subscribe only to needed data types

## Commercial Considerations

### Licensing
- **Health API**: Requires license fee payment for commercial applications
- **Activity API**: Commercial terms vary by use case
- **Developer Agreement**: Governs SDK and Program Material usage

### Rate Limiting
- Rate limits are implemented but specific thresholds not publicly documented
- Best practice: Use push notifications rather than constant polling
- Recommended to process PUSH/PING notifications when available

## Getting Started

### Application Process
1. Complete online developer application form
2. Provide complete and accurate business information
3. Wait for approval confirmation (typically within 2 business days)
4. Access Developer Portal upon approval
5. Download SDK and review documentation

### Required Information
- Business details and use case description
- Technical contact information
- Intended data usage and application type
- Agreement to maintain account in good standing

### Support Resources
- Developer web tools and sample data
- Auto-verification process before production deployment
- Developer forum and support email: `connect-support@developer.garmin.com`
- Comprehensive API documentation and guides

## Technical Requirements

### Development Environment
- Support for REST API integration
- OAuth 1.0a implementation capability
- JSON parsing for Health API data
- Binary file handling for FIT format (Activity API)

### Best Practices
- Implement proper error handling for rate limits
- Store OAuth tokens securely for reuse
- Use push notifications when possible to minimize API calls
- Implement retry logic with exponential backoff
- Respect user privacy and data usage agreements

## Limitations

### Access Restrictions
- Approval required for all API access
- Business use focus (personal projects may not qualify)
- Compliance with Garmin's terms of service required

### Data Access
- Users must explicitly consent to data sharing
- Data only available after device synchronization
- Some metrics require specific Garmin hardware

### Technical Constraints
- OAuth 1.0a implementation required (more complex than OAuth 2.0)
- Rate limiting can restrict high-frequency access
- Commercial licensing fees for certain use cases