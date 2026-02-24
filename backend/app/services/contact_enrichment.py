"""Contact enrichment service for auto-populating CRM data.

This module provides intelligent contact enrichment based on email patterns,
domain analysis, and external data sources.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Common email domains that don't indicate a company
PERSONAL_DOMAINS = frozenset({
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com",
    "icloud.com", "me.com", "mac.com", "aol.com", "protonmail.com",
    "pm.me", "zoho.com", "yandex.com", "mail.ru", "qq.com",
    "163.com", "126.com", "sina.com", "sohu.com", "foxmail.com",
})

# Title patterns to extract from email signatures
TITLE_PATTERNS = [
    r'(?i)(?:^|\n|\|)\s*([A-Z][a-zA-Z\s]{2,30}?)(?:\s*,\s*(?:MBA|PhD|MD|JD|CPA|CFA))?\s*(?:at|@|with)\s+',  # Name at Company
    r'(?i)(?:title|position)\s*[:\-]\s*([^\n]{2,50})',
]

# Company patterns
COMPANY_PATTERNS = [
    r'(?i)(?:company|organization)\s*[:\-]\s*([^\n]{2,50})',
]


def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    if "@" in email:
        return email.split("@")[-1].lower()
    return ""


def is_business_email(email: str) -> bool:
    """Check if email is from a business domain (not personal)."""
    domain = extract_domain(email)
    return domain and domain not in PERSONAL_DOMAINS


def extract_company_from_domain(email: str) -> str:
    """Extract potential company name from email domain.
    
    Examples:
        john@acme.com -> Acme
        jane@acme-corp.co.uk -> Acme Corp
        bob@api.hubspot.com -> Hubspot
    """
    domain = extract_domain(email)
    if not domain or domain in PERSONAL_DOMAINS:
        return ""
    
    # Remove subdomains (e.g., api.hubspot.com -> hubspot.com)
    parts = domain.split(".")
    if len(parts) > 2:
        # Check if it's a known TLD pattern
        if parts[-2] in ("co", "com", "org", "net", "gov", "edu", "ac"):
            main_domain = parts[-3]
        else:
            main_domain = parts[-2]
    else:
        main_domain = parts[0]
    
    # Clean up and format company name
    company = main_domain.replace("-", " ").replace("_", " ")
    company = re.sub(r'\d+$', '', company)  # Remove trailing numbers
    company = company.strip().title()
    
    return company


def extract_name_from_sender(sender: str) -> tuple[str, str]:
    """Extract first and last name from sender string.
    
    Examples:
        "John Doe" -> ("John", "Doe")
        "john@example.com" -> ("", "")
        '"Doe, John" <john@example.com>' -> ("John", "Doe")
    """
    # Extract name part before email
    if "<" in sender and ">" in sender:
        name_part = sender.split("<")[0].strip().strip('"')
    else:
        name_part = sender.strip()
    
    if not name_part or "@" in name_part:
        return "", ""
    
    # Handle "Last, First" format
    if "," in name_part:
        parts = name_part.split(",", 1)
        if len(parts) == 2:
            last = parts[0].strip()
            first = parts[1].strip()
            return first, last
    
    # Handle "First Last" format
    parts = name_part.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    
    # Single name
    return name_part, ""


def extract_title_from_body(body: str) -> str:
    """Attempt to extract job title from email body/signature."""
    for pattern in TITLE_PATTERNS:
        match = re.search(pattern, body)
        if match:
            title = match.group(1).strip()
            # Clean up common artifacts
            title = re.sub(r'\s+', ' ', title)
            if 2 < len(title) < 50:
                return title
    return ""


def extract_company_from_body(body: str) -> str:
    """Attempt to extract company from email body/signature."""
    for pattern in COMPANY_PATTERNS:
        match = re.search(pattern, body)
        if match:
            company = match.group(1).strip()
            if 2 < len(company) < 50:
                return company
    return ""


def enrich_contact_data(
    email: str,
    sender: str,
    body: str = "",
) -> dict[str, Any]:
    """Enrich contact data from available information.
    
    This function extracts as much information as possible from
    the email address, sender name, and body to populate CRM fields.
    
    Args:
        email: The contact's email address
        sender: The sender string (e.g., "John Doe <john@example.com>")
        body: Optional email body for additional extraction
        
    Returns:
        Dictionary with enriched contact data
    """
    first_name, last_name = extract_name_from_sender(sender)
    
    # Try to get company from domain
    company = extract_company_from_domain(email)
    
    # If body provided, try to extract more info
    title = ""
    if body:
        title = extract_title_from_body(body)
        if not company:
            company = extract_company_from_body(body)
    
    result = {
        "first_name": first_name,
        "last_name": last_name,
        "name": f"{first_name} {last_name}".strip(),
        "company": company,
        "title": title,
        "is_business_email": is_business_email(email),
        "domain": extract_domain(email),
    }
    
    logger.debug("Enriched contact data for %s: %s", email, result)
    return result


# Common company domain mappings (optional enhancement)
COMPANY_DOMAIN_MAPPINGS: dict[str, str] = {
    "google.com": "Google",
    "microsoft.com": "Microsoft",
    "amazon.com": "Amazon",
    "apple.com": "Apple",
    "facebook.com": "Meta",
    "meta.com": "Meta",
    "netflix.com": "Netflix",
    "salesforce.com": "Salesforce",
    "hubspot.com": "HubSpot",
    "zendesk.com": "Zendesk",
    "slack.com": "Slack",
    "stripe.com": "Stripe",
    "square.com": "Block",
    "twitter.com": "X",
    "x.com": "X",
    "linkedin.com": "LinkedIn",
}


def get_known_company(domain: str) -> str:
    """Get company name for known domains."""
    return COMPANY_DOMAIN_MAPPINGS.get(domain.lower(), "")
