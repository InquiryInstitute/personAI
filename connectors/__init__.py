"""Connectors package for data source integrations"""
from connectors.github import GitHubConnector
from connectors.drive import GoogleDriveConnector
from connectors.web import WebConnector

__all__ = ['GitHubConnector', 'GoogleDriveConnector', 'WebConnector']
