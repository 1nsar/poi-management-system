import unittest
from manager import POIManager, POI, is_equal, EPSILON
from models import SAMPLE_CONFIG

class TestPOIManager(unittest.TestCase):
    
    def setUp(self):
        """Set up the manager and load the sample config before each test."""
        # Ensure the POI ID counter is reset for predictable IDs (IDs 1-5 used in config)
        POI.next_poi_id = 1
        self.manager = POIManager()
        self.manager.load_config(SAMPLE_CONFIG)
        
        self.POI_IDS = {poi.name: poi.id for poi in self.manager.poi_registry.values()}
        self.VISITOR_IDS = {v.name: v.id for v in self.manager.visitors.values()}

    def test_1_id_non_reuse_and_type_deletion_constraint(self):
        """Test Case 1: POI ID Non-Reuse and Type Deletion Constraint."""
        
        # 1. Add temporary POI Type and POI
        self.manager.add_poi_type("TempType", {"feature": "str"})
        temp_poi_id = self.manager.add_poi("TempPOI", (10, 10), "TempType", {"feature": "A"}) # ID 6

        # Check constraint: cannot delete type if POIs exist
        with self.assertRaisesRegex(Exception, "Cannot delete POI Type"):
            self.manager.delete_poi_type("TempType")
            
        # 2. Delete the POI (ID 6)
        self.manager.delete_poi(temp_poi_id)
        next_id_after_delete = POI.next_poi_id # Should be 7

        # Create a new POI, its ID must be 7 (non-reused ID)
        self.manager.add_poi("NewPOI", (1, 1), "Park", {"size_sqm": 100, "has_playground": False})
        new_poi_id = self.manager.poi_registry[POI.next_poi_id - 1].id

        self.assertEqual(new_poi_id, next_id_after_delete, "Deleted ID was reused (ID non-reuse constraint failed)")

        # 3. Check type deletion after POIs are gone
        self.manager.delete_poi_type("TempType")
        self.assertNotIn("TempType", self.manager.poi_types, "POI Type deletion failed after POIs were removed")


    def test_2_boundary_correctness_pq6(self):
        """Test Case 2: Boundary Correctness (PQ6a/b) - POIs exactly at radius."""
        center = (500, 500)
        # POI 2: Central Green Park at (500, 500). Distance = 0.0
        # POI 3: The Spicy Spoon at (510, 500). Distance = 10.0

        # Test 1: Check POIs exactly at r=10.0
        boundary_r_10 = self.manager.query_pq6_boundary_correctness(center, 10.0)
        self.assertEqual(len(boundary_r_10), 1, "Should find 1 POI exactly at r=10.0")
        self.assertEqual(boundary_r_10[0]['id'], self.POI_IDS['The Spicy Spoon'], "Incorrect POI found at r=10.0 boundary")

        # Test 2: Check POIs exactly at r=0.0
        boundary_r_0 = self.manager.query_pq6_boundary_correctness(center, 0.0)
        self.assertEqual(len(boundary_r_0), 1, "Should find 1 POI exactly at r=0.0")
        self.assertEqual(boundary_r_0[0]['id'], self.POI_IDS['Central Green Park'], "Incorrect POI found at r=0.0 boundary")


    def test_3_distance_edge_case_pq4_pq5(self):
        """Test Case 3: Within Radius (PQ4) vs. K Nearest (PQ5) Consistency."""
        center = (100, 50) # Center on POI 1 (National History Museum)
        # POI 1: (100, 50). Dist=0.0
        # POI 4: (200, 50). Dist=100.0

        # Test 1: Within Radius (PQ4)
        r_100 = self.manager.query_pq4_within_radius(center, 100.0)
        self.assertEqual(len(r_100), 2, "PQ4 should find 2 POIs (0.0 and 100.0 distance)")
        self.assertTrue(is_equal(r_100[1]['distance'], 100.0), "PQ4 failed to include POI exactly at boundary 100.0")

        # Test 2: K Nearest (PQ5)
        k_2 = self.manager.query_pq5_k_nearest(center, 2)
        self.assertEqual(len(k_2), 2, "PQ5 should find 2 nearest POIs")
        self.assertEqual(k_2[0]['id'], self.POI_IDS['National History Museum'])
        self.assertEqual(k_2[1]['id'], self.POI_IDS['Art Gallery X'])


    def test_4_top_k_visitors_vq4_tie_breaking(self):
        """Test Case 4: Top K Visitors (VQ4) with Tie-breaking (ID then Name)."""
        # Ali Hassan: Unique POIs = 3 (1, 2, 4)
        # Lena Schmidt: Unique POIs = 3 (2, 3, 5)
        # Kenji Sato: Unique POIs = 2 (3, 5)
        
        ALI_ID = self.VISITOR_IDS['Ali Hassan']
        LENA_ID = self.VISITOR_IDS['Lena Schmidt']
        
        top_k_2 = self.manager.query_vq4_top_k_visitors(2)
        
        self.assertEqual(len(top_k_2), 2, "VQ4 should return 2 visitors")
        self.assertEqual(top_k_2[0]['poi_count'], 3)
        self.assertEqual(top_k_2[1]['poi_count'], 3)
        
        # Tie-break check: the visitor with the lexicographically smaller ID should be first.
        expected_first_id = min(ALI_ID, LENA_ID)
        self.assertEqual(top_k_2[0]['visitor_id'], expected_first_id, "VQ4 failed ID-based tie-breaking")


    def test_5_counting_rules_distinct_vs_repeat(self):
        """Test Case 5: Counting Rules (Distinct POIs vs. Repeat Visits)."""
        ALI_ID = self.VISITOR_IDS['Ali Hassan']
        
        # Ali Hassan visits: (1, 2, 4, 1-repeat). Total visits = 4. Unique POIs = 3.
        
        # VQ3: POIs per visitor (Must count DISTINCT POIs)
        vq3_result = self.manager.query_vq3_pois_per_visitor()
        ali_count = next(r['poi_count'] for r in vq3_result if r['visitor_id'] == ALI_ID)
        self.assertEqual(ali_count, 3, "VQ3 should count 3 unique POIs for Ali")
        
        # Check Total Visits (Raw Data Check for comparison)
        total_visits = len(self.manager.visitors[ALI_ID].visits)
        self.assertEqual(total_visits, 4, "Raw data shows 4 total visit events")


    def test_6_coverage_fairness_vq7(self):
        """Test Case 6: Coverage Fairness (VQ7) - m POIs across t POI Types."""
        # Ali/Lena: 3 unique POIs, 2 distinct types each.
        
        # Test 1: Check for m=3, t=2
        # Ali and Lena meet the criteria (3 >= 3 POIs, 2 >= 2 types).
        vq7_1_result = self.manager.query_vq7_coverage_fairness(m=3, t=2)
        self.assertEqual(len(vq7_1_result), 2, "VQ7 (m=3, t=2) should find 2 visitors")
        
        # Test 2: Check for m=3, t=3
        # No visitor meets the type criteria (max distinct types is 2).
        vq7_2_result = self.manager.query_vq7_coverage_fairness(m=3, t=3)
        self.assertEqual(len(vq7_2_result), 0, "VQ7 (m=3, t=3) should find 0 visitors")