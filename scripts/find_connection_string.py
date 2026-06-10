#!/usr/bin/env python
"""
find_connection_string.py - Helper to locate Azure AI Foundry connection string.

Usage:
    python scripts/find_connection_string.py

This script attempts to find or construct your Foundry project connection string
by trying these methods in order:
    1. Check .env file for AZURE_FOUNDRY_CONNECTION_STRING
    2. Query Azure Management API (requires Azure CLI login)
    3. Construct from known components
    4. Guide you to manually set it

Run this from project root directory.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def main():
    print("=" * 70)
    print("Azure AI Foundry Connection String Finder")
    print("=" * 70)
    print()
    
    # Load .env
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded .env file")
    else:
        print("⚠ No .env file found, using environment variables only")
    
    # Method 1: Check for existing connection string
    existing_conn = os.getenv("AZURE_FOUNDRY_CONNECTION_STRING")
    if existing_conn and existing_conn != "":
        print()
        print("✓ Found existing AZURE_FOUNDRY_CONNECTION_STRING in environment:")
        print(f"  {existing_conn}")
        return
    
    print()
    print("Method 1: Checking for existing connection string... ")
    print("  ✗ Not found")
    
    # Method 2: Try to query Azure Management API
    print()
    print("Method 2: Querying Azure Management API...")
    try:
        from azure.identity import AzureCliCredential, ClientSecretCredential
        from azure.mgmt.machinelearningservices import MachineLearningServicesMgmtClient
        
        try:
            # Try Azure CLI first (easiest for local dev)
            credential = AzureCliCredential()
            print("  ✓ Azure CLI authenticated")
        except Exception as e:
            print(f"  ⚠ Azure CLI not available: {e}")
            credential = None
        
        if credential:
            subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
            if not subscription_id:
                print("  ✗ AZURE_SUBSCRIPTION_ID not set, cannot query")
            else:
                try:
                    client = MachineLearningServicesMgmtClient(credential, subscription_id)
                    rg = os.getenv("AZURE_FOUNDRY_RESOURCE_GROUP", "rg-arungajapathi-3294")
                    hub = os.getenv("AZURE_FOUNDRY_HUB", "certops-ai-resource")
                    
                    workspace = client.workspaces.get(rg, hub)
                    print(f"  ✓ Found workspace: {workspace.name}")
                    print(f"    Location: {workspace.location}")
                    print(f"    Resource Group: {rg}")
                    
                    # Construct connection string
                    region = workspace.location.lower().replace(" ", "")
                    conn_str = f"{region}.api.azureml.ms;{subscription_id};{rg};{hub}"
                    print()
                    print("✓ Constructed connection string:")
                    print(f"  {conn_str}")
                    print()
                    print("Add this to your .env file:")
                    print(f"  AZURE_FOUNDRY_CONNECTION_STRING={conn_str}")
                    return
                except Exception as e:
                    print(f"  ✗ Failed to query workspace: {e}")
    
    except ImportError:
        print("  ⚠ Azure SDK not installed (install with: pip install azure-mgmt-machinelearningservices)")
    
    # Method 3: Construct from components
    print()
    print("Method 3: Constructing from environment variables...")
    
    hub = os.getenv("AZURE_FOUNDRY_HUB", "certops-ai-resource")
    rg = os.getenv("AZURE_FOUNDRY_RESOURCE_GROUP", "rg-arungajapathi-3294")
    sub = os.getenv("AZURE_SUBSCRIPTION_ID")
    region = os.getenv("AZURE_FOUNDRY_REGION", "eastus")
    
    if sub:
        conn_str = f"{region}.api.azureml.ms;{sub};{rg};{hub}"
        print(f"  ✓ Constructed from components:")
        print(f"    Hub: {hub}")
        print(f"    Resource Group: {rg}")
        print(f"    Subscription: {sub}")
        print(f"    Region: {region}")
        print()
        print("Connection string:")
        print(f"  {conn_str}")
        print()
        print("Add this to your .env file:")
        print(f"  AZURE_FOUNDRY_CONNECTION_STRING={conn_str}")
    else:
        print("  ✗ AZURE_SUBSCRIPTION_ID not set")
    
    # Guide user
    print()
    print("=" * 70)
    print("To set up Foundry IQ integration:")
    print()
    print("1. Get your Subscription ID:")
    print("   az account show --query id")
    print()
    print("2. Add to .env file:")
    print("   AZURE_SUBSCRIPTION_ID=your-subscription-id")
    print("   AZURE_FOUNDRY_CONNECTION_STRING=region.api.azureml.ms;sub-id;rg;hub")
    print()
    print("3. Verify by running this script again:")
    print("   python scripts/find_connection_string.py")
    print()
    print("4. Test in Python:")
    print("   from backend.plugins.foundry_knowledge_plugin import FoundryKnowledgePlugin")
    print("   plugin = FoundryKnowledgePlugin()")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
