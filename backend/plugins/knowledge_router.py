"""
knowledge_router.py - Centralized knowledge plugin factory.
Selects between FoundryKnowledgePlugin and DynamicKnowledgePlugin based on configuration.
"""
import os


def get_knowledge_plugin():
    """
    Get the appropriate knowledge plugin based on configuration.
    
    Returns:
        FoundryKnowledgePlugin if USE_FOUNDRY_IQ=true, otherwise DynamicKnowledgePlugin
    """
    use_foundry = os.getenv("USE_FOUNDRY_IQ", "true").lower() == "true"
    
    if use_foundry:
        try:
            from backend.plugins.foundry_knowledge_plugin import FoundryKnowledgePlugin
            print("[Router] Using FoundryKnowledgePlugin (primary)")
            return FoundryKnowledgePlugin()
        except Exception as e:
            print(f"[Router] FoundryKnowledgePlugin failed to init: {e}, falling back to Dynamic")
    
    # Fallback to DynamicKnowledgePlugin
    try:
        from backend.plugins.dynamic_knowledge_plugin import DynamicKnowledgePlugin
        print("[Router] Using DynamicKnowledgePlugin")
        return DynamicKnowledgePlugin()
    except Exception as e:
        print(f"[Router] DynamicKnowledgePlugin failed: {e}")
        raise RuntimeError("No knowledge plugin available")
