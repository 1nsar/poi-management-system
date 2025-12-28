import uuid
from typing import Dict, List, Tuple, Any, Optional

# --- Data Structures (Models) ---

class POIType:
    """Represents a type of Point of Interest (e.g., 'Museum')."""
    def __init__(self, name: str, attributes: Dict[str, str]):
        self.name = name
        # Attributes is a dict of {attribute_name: data_type}
        self.attributes = attributes

    def __repr__(self):
        return f"POIType(name='{self.name}', attrs={list(self.attributes.keys())})"

class POI:
    """Represents a Point of Interest (POI)."""
    # next_poi_id is a static counter to ensure unique, non-reusable IDs (Constraint).
    next_poi_id = 1

    def __init__(self, name: str, location: Tuple[int, int], poi_type_name: str, attributes: Dict[str, Any]):
        # POI identifiers: Each POI has a unique identifier that is never reused.
        self.id = POI.next_poi_id
        POI.next_poi_id += 1
        
        # Name and location are immutable (not updatable) as per constraint.
        self.name = name
        self.location = location
        self.poi_type_name = poi_type_name
        self.attributes = attributes
        
    def __repr__(self):
        return f"POI(id={self.id}, name='{self.name}', type='{self.poi_type_name}', loc={self.location})"

class Visitor:
    """Represents a Visitor and their visits to POIs."""
    def __init__(self, name: str, nationality: str):
        # Unique ID for visitor
        self.id = str(uuid.uuid4()) 
        self.name = name
        self.nationality = nationality
        
        # List of visits: (poi_id, date: str, rating: Optional[int])
        self.visits: List[Tuple[int, str, Optional[int]]] = []

    def __repr__(self):
        return f"Visitor(id='{self.id[:8]}...', name='{self.name}', nationality='{self.nationality}')"

# --- Sample Configuration Data ---

# This structure mimics the data loaded from a config file.
SAMPLE_CONFIG = {
    "poi_types": {
        "Museum": {"attributes": {"collections": "str", "year_opened": "int"}},
        "Park": {"attributes": {"size_sqm": "int", "has_playground": "bool"}},
        "Restaurant": {"attributes": {"cuisine": "str", "rating": "float"}}
    },
    "pois": [
        {"name": "National History Museum", "location": [100, 50], "type": "Museum", 
         "attributes": {"collections": "Ancient Artifacts", "year_opened": 1980}}, # ID 1
        {"name": "Central Green Park", "location": [500, 500], "type": "Park", 
         "attributes": {"size_sqm": 50000, "has_playground": True}}, # ID 2
        {"name": "The Spicy Spoon", "location": [510, 500], "type": "Restaurant", 
         "attributes": {"cuisine": "Indian", "rating": 4.5}}, # ID 3
        {"name": "Art Gallery X", "location": [200, 50], "type": "Museum", 
         "attributes": {"collections": "Modern Art", "year_opened": 2010}}, # ID 4
        {"name": "Sushi Heaven", "location": [800, 100], "type": "Restaurant", 
         "attributes": {"cuisine": "Japanese", "rating": 4.9}}, # ID 5
    ],
    "visitors": [
        {"name": "Ali Hassan", "nationality": "UAE", "visits": [
            {"poi_id": 1, "date": "15/01/2024", "rating": 8},
            {"poi_id": 2, "date": "16/01/2024"}, 
            {"poi_id": 4, "date": "17/01/2024", "rating": 9},
            {"poi_id": 1, "date": "18/01/2024", "rating": 7}, 
        ]},
        {"name": "Lena Schmidt", "nationality": "Germany", "visits": [
            {"poi_id": 2, "date": "01/02/2024", "rating": 10},
            {"poi_id": 3, "date": "02/02/2024", "rating": 6},
            {"poi_id": 5, "date": "03/02/2024", "rating": 9},
        ]},
        {"name": "Kenji Sato", "nationality": "Japan", "visits": [
            {"poi_id": 5, "date": "10/02/2024", "rating": 10},
            {"poi_id": 3, "date": "11/02/2024", "rating": 7},
        ]},
    ]
}