# Kapture Maya Voice Agent

AI-powered voice collections agent for Kapture Finance, built with Vapi, Flask, and SQLite, featuring customer verification, OTP authentication, payment assistance, PTP logging, escalation, and call disposition.

## Architecture

Vapi / Maya
    ↓
Flask REST APIs
    ↓
SQLite Database

The Flask backend provides controlled business APIs that can be called by the Vapi voice agent.

## Tech Stack

- Python
- Flask
- SQLite
- Flask-CORS
- Vapi
- REST APIs

## Features

- Customer identification using registered phone number
- OTP-based customer verification
- Secure authentication flow
- Promise-to-Pay logging
- Mock payment-link generation
- Call disposition tracking
- Human-agent escalation
- SQLite-based customer and loan data

## API Endpoints

### 1. Verify Customer

```http
POST /api/verify-customer
