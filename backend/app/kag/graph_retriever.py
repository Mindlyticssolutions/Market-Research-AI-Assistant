"""
KAG Graph Retriever
Uses Azure Cosmos DB Gremlin API for Knowledge Graph retrieval in the AI Assistant
"""
from typing import List, Dict, Any, Optional
from gremlin_python.driver import client as gremlin_client
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

from app.core.config import settings
import sys
import asyncio

# Windows workaround for gremlin-python on Python 3.8+
if sys.platform == 'win32':
    try:
        if isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


class KAGRetriever:
    """
    Retriever for KAG using Azure Cosmos DB Gremlin
    Used by AI Assistant agents to access knowledge graph context
    """
    
    def __init__(self):
        self.endpoint = settings.COSMOS_GREMLIN_ENDPOINT
        self.key = settings.COSMOS_GREMLIN_KEY
        self.database = settings.COSMOS_GREMLIN_DATABASE
        self.graph = settings.COSMOS_GREMLIN_GRAPH
        self._client = None
    
    def _get_client(self):
        """Get Gremlin client"""
        if self._client is None:
            if not self.endpoint or not self.key:
                raise ValueError("Cosmos DB Gremlin not configured")
            
            # Build connection URL
            url = self.endpoint
            if not url.startswith("wss://"):
                host = url.replace("https://", "").replace("/", "")
                url = f"wss://{host}:443/"
            
            username = f"/dbs/{self.database}/colls/{self.graph}"
            
            self._client = gremlin_client.Client(
                url=url,
                traversal_source='g',
                username=username,
                password=self.key,
                message_serializer=gremlin_client.serializer.GraphSONSerializersV2d0()
            )
        return self._client
    
    async def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a Gremlin query asynchronously"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def _run_query():
            try:
                print(f"DEBUG: [KAGRetriever] Getting client...")
                client = self._get_client()
                print(f"DEBUG: [KAGRetriever] Submitting query: {query[:50]}...")
                result_set = client.submit(query)
                print(f"DEBUG: [KAGRetriever] Query submitted, waiting for results...")
                results = result_set.all().result()
                print(f"DEBUG: [KAGRetriever] Query complete. Returned {len(results) if results else 0} results.")
                return results
            except Exception as e:
                print(f"DEBUG: [KAGRetriever] Gremlin query error: {e}")
                return []

        try:
            print(f"DEBUG: [KAGRetriever] Running _run_query in executor...")
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _run_query)
            print(f"DEBUG: [KAGRetriever] Executor returned.")
            return results
        except Exception as e:
            print(f"Gremlin execution error: {e}")
            return []
    
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant entities and relationships from knowledge graph
        
        Args:
            query: Search query (used to find matching entities)
            top_k: Maximum number of results
            
        Returns:
            List of entities/relationships with properties
        """
        try:
            # Search for vertices containing query terms
            # Using case-insensitive contains for flexibility
            search_term = query.lower().replace("'", "\\'")
            
            # Find vertices with matching labels or properties
            # STRICT METADATA ONLY: Project only ID, Label, and Name
            gremlin_query = f"""
                g.V()
                .has('name', containing('{search_term}'))
                .limit({top_k})
                .project('id', 'label', 'name')
                .by(id())
                .by(label())
                .by(values('name').fold())
            """
            
            results = await self._execute_query(gremlin_query)
            
            # Format results
            entities = []
            for result in results:
                entities.append({
                    "id": result.get("id", ""),
                    "label": result.get("label", ""),
                    "name": result.get("name", [""])[0] if result.get("name") else "",
                    "properties": result.get("properties", {}),
                    "type": "vertex"
                })
            
            return entities
            
        except Exception as e:
            print(f"KAG retrieval error: {e}")
            return []
    
    async def get_relationships(
        self, 
        entity_id: str, 
        direction: str = "both",
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific entity
        
        Args:
            entity_id: ID of the entity
            direction: 'in', 'out', or 'both'
            top_k: Maximum relationships to return
        """
        try:
            if direction == "out":
                gremlin_query = f"g.V('{entity_id}').outE().limit({top_k}).project('label', 'target').by(label()).by(inV().values('name'))"
            elif direction == "in":
                gremlin_query = f"g.V('{entity_id}').inE().limit({top_k}).project('label', 'source').by(label()).by(outV().values('name'))"
            else:
                gremlin_query = f"g.V('{entity_id}').bothE().limit({top_k}).project('label', 'other').by(label()).by(otherV().values('name'))"
            
            results = await self._execute_query(gremlin_query)
            
            relationships = []
            for result in results:
                relationships.append({
                    "relation": result.get("label", ""),
                    "connected_entity": result.get("target") or result.get("source") or result.get("other", ""),
                    "type": "edge"
                })
            
            return relationships
            
        except Exception as e:
            print(f"KAG relationship error: {e}")
            return []
    
    async def get_subgraph(
        self, 
        entity_name: str, 
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Get a subgraph centered on an entity
        
        Args:
            entity_name: Name of the central entity
            depth: How many hops to traverse
        """
        try:
            # Find entity and get its neighborhood
            gremlin_query = f"""
                g.V()
                .has('name', '{entity_name}')
                .repeat(both().simplePath())
                .times({depth})
                .path()
                .limit(20)
            """
            
            results = await self._execute_query(gremlin_query)
            
            return {
                "center": entity_name,
                "depth": depth,
                "paths": results
            }
            
        except Exception as e:
            print(f"KAG subgraph error: {e}")
            return {"center": entity_name, "depth": depth, "paths": []}
    
    def health_check(self) -> bool:
        """Check if the retriever is properly configured"""
        try:
            _ = self._get_client()
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the client connection"""
        if self._client:
            self._client.close()
            self._client = None
