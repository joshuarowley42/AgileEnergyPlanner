"""Octopus API Client

The API client for talking to Octopus Energy.

There are 2 classes here - OctopusAPIClient (in .octopus_api) and OctopusClient (in .octopus_data).

OctopusAPIClient is the raw API client.
OctopusClient is a subclass that adds caching and some meta functions.

Strongly suggest always using the latter.

"""
from .octopus_data import OctopusClient
