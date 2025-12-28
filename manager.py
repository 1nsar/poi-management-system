import math
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from models import POI, POIType, Visitor, SAMPLE_CONFIG

# --- Configuration and Constants ---
# Epsilon for robust floating-point comparisons (Boundary Correctness - PQ6b)
EPSILON = 1e-6 
MAP_SIZE = 1000 # Map is 1000x1000 grid (coordinates 0 to 999)

# --- Utility Functions ---

def euclidean_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    """Calculates the Euclidean distance between two points."""
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def is_equal(a: float, b: float, epsilon: float = EPSILON) -> bool:
    """Implements a robust comparison strategy for floating-point calculations (PQ6b)."""
    return abs(a - b) < epsilon

# --- Core POI Management System ---

class POIManager:
    """Manages all POIs, POI Types, and Visitor data."""
    def __init__(self):
        self.poi_types: Dict[str, POIType] = {}
        self.poi_registry: Dict[int, POI] = {} # POIs stored by immutable ID
        self.visitors: Dict[str, Visitor] = {} # Visitors stored by ID
        
        # The POI.next_poi_id counter itself handles non-reuse, but we reset it 
        # when initializing to ensure deterministic IDs for testing.
        POI.next_poi_id = 1 

    # --- Initialization & Configuration ---
    
    def load_config(self, config_data: Dict[str, Any]):
        """Loads initial configuration data from a dictionary (SAMPLE_CONFIG)."""
        print("--- Loading Configuration ---")
        
        # 1. Load POI Types
        for type_name, attrs in config_data.get('poi_types', {}).items():
            try:
                self.add_poi_type(type_name, attrs['attributes'])
            except Exception as e:
                print(f"Config Error: Could not load POI type '{type_name}': {e}")
        
        # 2. Load POIs
        for poi_data in config_data.get('pois', []):
            try:
                name = poi_data['name']
                location = tuple(poi_data['location'])
                poi_type_name = poi_data['type']
                attributes = poi_data['attributes']
                self.add_poi(name, location, poi_type_name, attributes)
            except Exception as e:
                print(f"Config Error: Could not load POI '{poi_data.get('name', 'N/A')}': {e}")

        # 3. Load Visitors and Visits
        for visitor_data in config_data.get('visitors', []):
            try:
                visitor = Visitor(visitor_data['name'], visitor_data['nationality'])
                self.visitors[visitor.id] = visitor
                
                for visit_data in visitor_data.get('visits', []):
                    poi_id = visit_data['poi_id']
                    date = visit_data['date']
                    rating = visit_data.get('rating')
                    # Use the visitor object's ID for recording the visit
                    self.add_visit(visitor.id, poi_id, date, rating, quiet=True) 
            except Exception as e:
                print(f"Config Error: Could not load Visitor '{visitor_data.get('name', 'N/A')}' or their visits: {e}")
        
        print("--- Configuration Loading Complete ---")

    # --- Core Operations (CRUD) ---

    def add_poi_type(self, name: str, attributes: Dict[str, str]):
        """Adds a new POI type."""
        if name in self.poi_types:
            raise ValueError(f"POI Type '{name}' already exists.")
        self.poi_types[name] = POIType(name, attributes)

    def delete_poi_type(self, type_name: str):
        """
        Deletes a POI type. Constraint: A type can be deleted only if no POIs 
        of that type exist (Type deletion only if no POIs).
        """
        if type_name not in self.poi_types:
            raise ValueError(f"POI Type '{type_name}' does not exist.")
        
        if any(poi.poi_type_name == type_name for poi in self.poi_registry.values()):
            raise Exception(f"Cannot delete POI Type '{type_name}': Existing POIs of this type found.")
        
        del self.poi_types[type_name]
        print(f"Successfully deleted POI Type: {type_name}")

    def add_poi(self, name: str, location: Tuple[int, int], poi_type_name: str, attributes: Dict[str, Any]):
        """Adds a new POI, assigning a unique, non-reusable ID."""
        if poi_type_name not in self.poi_types:
            raise ValueError(f"POI Type '{poi_type_name}' is not defined.")
        
        # Map boundary validation
        if not (0 <= location[0] < MAP_SIZE and 0 <= location[1] < MAP_SIZE):
            raise ValueError(f"Location {location} is outside the {MAP_SIZE}x{MAP_SIZE} map grid.")

        new_poi = POI(name, location, poi_type_name, attributes)
        self.poi_registry[new_poi.id] = new_poi
        
        print(f"Successfully added POI: {new_poi}")
        return new_poi.id

    def delete_poi(self, poi_id: int):
        """Deletes a POI. Its ID is permanently tracked (non-reusable ID constraint)."""
        if poi_id not in self.poi_registry:
            raise ValueError(f"POI with ID {poi_id} not found.")
        
        poi_name = self.poi_registry[poi_id].name
        del self.poi_registry[poi_id]
        print(f"Successfully deleted POI: {poi_name} (ID: {poi_id})")

    def add_visitor(self, name: str, nationality: str) -> str:
        """Adds a new visitor."""
        new_visitor = Visitor(name, nationality)
        self.visitors[new_visitor.id] = new_visitor
        print(f"Successfully added Visitor: {new_visitor}")
        return new_visitor.id

    def add_visit(self, visitor_id: str, poi_id: int, date: str, rating: Optional[int] = None, quiet: bool = False):
        """Records a visit event for a visitor to a POI."""
        if visitor_id not in self.visitors:
            raise ValueError(f"Visitor with ID {visitor_id} not found.")
        if poi_id not in self.poi_registry:
            # Only raise error if the POI is supposed to exist, ignore if it was deleted.
            if not quiet:
                print(f"Warning: POI with ID {poi_id} not found in current registry. Recording visit anyway.")
        
        # Optional validation for date format
        try:
            datetime.strptime(date, '%d/%m/%Y')
        except ValueError:
            if not quiet:
                print(f"Warning: Date format is not dd/mm/yyyy for visit to POI {poi_id}.")
        
        # Optional validation for rating (1-10)
        if rating is not None and not (1 <= rating <= 10):
            if not quiet:
                print(f"Warning: Rating {rating} is outside the 1-10 range for visit to POI {poi_id}.")

        self.visitors[visitor_id].visits.append((poi_id, date, rating))
        if not quiet:
            print(f"Visit recorded for Visitor {self.visitors[visitor_id].name} to POI {poi_id}.")


    # --- Queries for POIS (PQ) ---

    def query_pq1_list_by_type(self, poi_type_name: str) -> List[Dict[str, Any]]:
        """PQ1: For a specific POI type, list the POIs with all attribute values."""
        if poi_type_name not in self.poi_types:
            raise ValueError(f"POI Type '{poi_type_name}' not found.")
            
        results = []
        for poi in self.poi_registry.values():
            if poi.poi_type_name == poi_type_name:
                results.append({
                    'id': poi.id,
                    'name': poi.name,
                    'location': poi.location,
                    'attributes': poi.attributes,
                })
        return results

    def query_pq2_closest_pair(self) -> Optional[Tuple[float, Tuple[POI, POI]]]:
        """PQ2: Find the pair of POIs with the minimum pair-wise Euclidean distance."""
        pois = list(self.poi_registry.values())
        min_dist = float('inf')
        closest_pair = None

        if len(pois) < 2:
            return None

        # O(n^2) check
        for i in range(len(pois)):
            for j in range(i + 1, len(pois)):
                poi1 = pois[i]
                poi2 = pois[j]
                
                distance = euclidean_distance(poi1.location, poi2.location)
                
                if distance < min_dist:
                    min_dist = distance
                    closest_pair = (poi1, poi2)
        
        if closest_pair:
            return (min_dist, closest_pair)
        return None

    def query_pq3_count_by_type(self) -> List[Tuple[str, int]]:
        """PQ3: Print the number of POIs per POI type."""
        counts = {name: 0 for name in self.poi_types.keys()}
            
        for poi in self.poi_registry.values():
            counts[poi.poi_type_name] = counts.get(poi.poi_type_name, 0) + 1
            
        # Sort by POI type name for deterministic ordering
        return sorted(counts.items())

    def _get_poi_distances(self, center: Tuple[int, int]) -> List[Tuple[POI, float]]:
        """Helper to calculate distance for all POIs from a center point."""
        poi_distances = []
        for poi in self.poi_registry.values():
            distance = euclidean_distance(center, poi.location)
            poi_distances.append((poi, distance))
        return poi_distances

    def query_pq4_within_radius(self, center: Tuple[int, int], radius: float) -> List[Dict[str, Any]]:
        """
        PQ4: Given a map location and a radius r, list all POIs within 
        distance AT MOST r from c0. Uses robust comparison (PQ6b).
        """
        results = []
        for poi, distance in self._get_poi_distances(center):
            # Check for distance <= radius, using epsilon for robustness (PQ6b)
            if distance < radius or is_equal(distance, radius):
                results.append({
                    'id': poi.id,
                    'name': poi.name,
                    'location': poi.location,
                    'type': poi.poi_type_name,
                    'distance': distance,
                })
        
        # Sort by distance, then ID for deterministic ordering
        results.sort(key=lambda x: (x['distance'], x['id'], x['name']))
        return results

    def query_pq5_k_nearest(self, center: Tuple[int, int], k: int) -> List[Dict[str, Any]]:
        """
        PQ5: Given c0 and an integer k, list the k POIs closest to c0 in 
        increasing distance order.
        """
        poi_distances = self._get_poi_distances(center)
        
        # Sort by distance (ascending), then ID (ascending), then name (ascending) for tie-breaking
        poi_distances.sort(key=lambda x: (x[1], x[0].id, x[0].name))
        
        results = []
        for poi, distance in poi_distances[:k]:
            results.append({
                'id': poi.id,
                'name': poi.name,
                'location': poi.location,
                'type': poi.poi_type_name,
                'distance': distance,
            })
        
        return results

    def query_pq6_boundary_correctness(self, center: Tuple[int, int], radius: float) -> List[Dict[str, Any]]:
        """
        PQ6a: For a given c0 and radius r, list POIs exactly at distance r from c0.
        Uses the robust comparison strategy (PQ6b) with EPSILON.
        """
        results = []
        for poi, distance in self._get_poi_distances(center):
            # Check for distance EXACTLY equal to radius, using epsilon
            if is_equal(distance, radius):
                results.append({
                    'id': poi.id,
                    'name': poi.name,
                    'location': poi.location,
                    'type': poi.poi_type_name,
                    'distance': distance,
                })

        # Sort by ID, then name for deterministic ordering
        results.sort(key=lambda x: (x['id'], x['name']))
        return results


    # --- Queries for Visitors and POIs (VQ) ---

    def query_vq1_visitor_visits(self, visitor_id: str) -> List[Dict[str, Any]]:
        """VQ1: For a specific visitor, list all the visited POIs (id, name, date)."""
        if visitor_id not in self.visitors:
            raise ValueError(f"Visitor with ID {visitor_id} not found.")

        visitor = self.visitors[visitor_id]
        results = []
        for poi_id, date, _ in visitor.visits:
            poi = self.poi_registry.get(poi_id)
            if poi: # Only list existing POIs
                results.append({
                    'poi_id': poi_id,
                    'poi_name': poi.name,
                    'date': date,
                })
        
        # Sort by date for presentation
        results.sort(key=lambda x: datetime.strptime(x['date'], '%d/%m/%Y'), reverse=True)
        return results

    def _get_poi_visit_counts(self) -> Dict[int, int]:
        """Helper to count unique visitors per POI (Distinct by default)."""
        poi_visitors: Dict[int, set] = {}
        for visitor in self.visitors.values():
            # Set of POI IDs visited by this visitor (ensures distinct visitor count per POI)
            visited_poi_ids = set(visit[0] for visit in visitor.visits)
            for poi_id in visited_poi_ids:
                if poi_id in self.poi_registry: 
                    poi_visitors.setdefault(poi_id, set()).add(visitor.id)
        
        return {poi_id: len(v_ids) for poi_id, v_ids in poi_visitors.items()}


    def _get_visitor_poi_counts(self) -> Dict[str, int]:
        """Helper to count unique POIs visited per visitor (Distinct by default)."""
        visitor_poi_counts = {}
        for visitor in self.visitors.values():
            # Get unique POI IDs visited by this visitor, only counting existing POIs
            unique_poi_ids = set(visit[0] for visit in visitor.visits if visit[0] in self.poi_registry)
            visitor_poi_counts[visitor.id] = len(unique_poi_ids)
        return visitor_poi_counts


    def query_vq2_visitors_per_poi(self) -> List[Dict[str, Any]]:
        """VQ2: Print the number of unique visitors per POI."""
        poi_counts = self._get_poi_visit_counts()
        
        results = []
        for poi_id, count in poi_counts.items():
            poi = self.poi_registry[poi_id]
            results.append({
                'poi_id': poi_id,
                'poi_name': poi.name,
                'visitor_count': count,
            })
            
        # Deterministic ordering: by POI ID (ascending), then name (ascending)
        results.sort(key=lambda x: (x['poi_id'], x['poi_name']))
        return results

    def query_vq3_pois_per_visitor(self) -> List[Dict[str, Any]]:
        """VQ3: Print the number of unique POIs per visitor."""
        visitor_counts = self._get_visitor_poi_counts()
        
        results = []
        for visitor_id, count in visitor_counts.items():
            visitor = self.visitors[visitor_id]
            results.append({
                'visitor_id': visitor_id,
                'visitor_name': visitor.name,
                'poi_count': count,
            })
            
        # Deterministic ordering: by Visitor ID (ascending), then name (ascending)
        results.sort(key=lambda x: (x['visitor_id'], x['visitor_name']))
        return results

    def query_vq4_top_k_visitors(self, k: int) -> List[Dict[str, Any]]:
        """VQ4: List the k visitors who have visited the largest number of POIs."""
        visitor_counts = self._get_visitor_poi_counts()
        
        sortable_visitors = []
        for v_id, count in visitor_counts.items():
            visitor = self.visitors[v_id]
            sortable_visitors.append((count, v_id, visitor.name))

        # Sort: by count (descending), then ID (ascending), then name (ascending)
        sortable_visitors.sort(key=lambda x: (-x[0], x[1], x[2]))
        
        results = []
        for count, v_id, name in sortable_visitors[:k]:
            results.append({
                'visitor_id': v_id,
                'visitor_name': name,
                'poi_count': count,
            })
            
        return results

    def query_vq5_top_k_pois(self, k: int) -> List[Dict[str, Any]]:
        """VQ5: List the k POIs that have the largest number of visitors."""
        poi_counts = self._get_poi_visit_counts()

        sortable_pois = []
        for poi_id, count in poi_counts.items():
            poi = self.poi_registry[poi_id]
            sortable_pois.append((count, poi_id, poi.name))

        # Sort: by count (descending), then ID (ascending), then name (ascending)
        sortable_pois.sort(key=lambda x: (-x[0], x[1], x[2]))

        results = []
        for count, poi_id, name in sortable_pois[:k]:
            results.append({
                'poi_id': poi_id,
                'poi_name': name,
                'visitor_count': count,
            })

        return results

    def query_vq7_coverage_fairness(self, m: int, t: int) -> List[Dict[str, Any]]:
        """
        VQ7: Coverage fairness. List visitors who visited at least m unique POIs 
        across at least t distinct POI types.
        """
        results = []
        
        for visitor in self.visitors.values():
            unique_poi_ids = set(visit[0] for visit in visitor.visits)
            
            # Filter for only existing POIs
            existing_poi_ids = [pid for pid in unique_poi_ids if pid in self.poi_registry]
            
            total_pois_visited = len(existing_poi_ids)
            
            if total_pois_visited < m:
                continue 

            distinct_poi_types = set(self.poi_registry[pid].poi_type_name for pid in existing_poi_ids)
            num_distinct_types = len(distinct_poi_types)
            
            if num_distinct_types >= t:
                # Visitor meets both criteria
                results.append({
                    'visitor_id': visitor.id,
                    'name': visitor.name,
                    'nationality': visitor.nationality,
                    'total_pois_visited': total_pois_visited,
                    'num_distinct_poi_types': num_distinct_types,
                })

        # Deterministic ordering: by Visitor ID (ascending), then name (ascending)
        results.sort(key=lambda x: (x['visitor_id'], x['name']))
        return results