import json
import unittest
from manager import POIManager, POI
from models import SAMPLE_CONFIG
from tests import TestPOIManager # Import the test suite

# Set the initial POI ID to start from 1 for deterministic loading/testing
POI.next_poi_id = 1 
manager = POIManager()

def display_menu():
    """Prints the main menu options."""
    print("\n" + "="*40)
    print("POI MANAGEMENT SYSTEM - MENU")
    print(f"Total POIs: {len(manager.poi_registry)}, Total Visitors: {len(manager.visitors)}")
    print("=" * 40)
    print("CORE OPERATIONS:")
    print(" 1. Run Unit Tests (Resets data)")
    print(" 2. Reload Sample Configuration (Resets data)")
    print(" 3. Add New POI (Point of Interest)")
    print(" 4. Delete POI by ID")
    print(" 5. Add New Visitor")
    print(" 6. Record New Visit (POI ID, Visitor ID)")
    print(" 7. Delete POI Type (Must have 0 POIs)")
    print("\nPOI QUERIES (PQ):")
    print(" 8. PQ1: List POIs by Type")
    print(" 9. PQ2: Find Closest Pair of POIs")
    print("10. PQ3: Count POIs per POI Type")
    print("11. PQ4: List POIs Within Radius (<=r)")
    print("12. PQ5: List K Nearest POIs")
    print("13. PQ6: List POIs Exactly At Boundary (r)")
    print("\nVISITOR & POI QUERIES (VQ):")
    print("14. VQ1: List Visited POIs for a Visitor")
    print("15. VQ2: Count Visitors per POI")
    print("16. VQ3: Count POIs per Visitor")
    print("17. VQ4: List Top K Visitors (most POIs)")
    print("18. VQ5: List Top K POIs (most Visitors)")
    print("19. VQ7: Coverage Fairness (m POIs, t Types)")
    print("-" * 40)
    print(" 0. Exit")
    print("-" * 40)

def main_cli():
    """Main command line interface loop."""
    
    # Load initial data automatically on start
    manager.load_config(SAMPLE_CONFIG)

    while True:
        display_menu()
        choice = input("Enter your choice (0-19): ").strip()

        try:
            if choice == '0':
                print("Exiting POI Management System. Goodbye!")
                break
            elif choice == '1':
                # Run unit tests
                print("\n" + "="*50)
                print("RUNNING UNIT TESTS")
                print("="*50)
                # Note: Test run resets the manager state internally in setUp, 
                # but we'll reload config afterward to keep the CLI usable.
                suite = unittest.TestLoader().loadTestsFromTestCase(TestPOIManager)
                unittest.TextTestRunner(verbosity=2).run(suite)
                print("="*50)
                # Reload config to restore state after testing
                POI.next_poi_id = 1
                manager.__init__()
                manager.load_config(SAMPLE_CONFIG)
            
            elif choice == '2':
                # Reset and reload config
                POI.next_poi_id = 1
                manager.__init__()
                manager.load_config(SAMPLE_CONFIG)
            
            # --- CORE OPERATIONS (Abbreviated for brevity) ---
            elif choice == '3':
                name = input("Enter POI Name: ")
                x = int(input("Enter X coordinate (0-999): "))
                y = int(input("Enter Y coordinate (0-999): "))
                poi_type_names = list(manager.poi_types.keys())
                poi_type = input(f"Enter POI Type Name (Options: {', '.join(poi_type_names)}): ")
                attrs_input = input("Enter attributes as JSON string (e.g., '{\"collections\": \"New Art\"}'): ")
                attributes = json.loads(attrs_input)
                manager.add_poi(name, (x, y), poi_type, attributes)
            
            elif choice == '4':
                poi_id = int(input("Enter POI ID to delete: "))
                manager.delete_poi(poi_id)

            elif choice == '5':
                name = input("Enter Visitor Name: ")
                nationality = input("Enter Nationality: ")
                manager.add_visitor(name, nationality)

            elif choice == '6':
                poi_id = int(input("Enter POI ID: "))
                # Display available visitor IDs
                visitor_names = [f"{v.name} ({v.id[:4]}...)" for v in manager.visitors.values()]
                print(f"Known Visitors: {', '.join(visitor_names)}")
                visitor_id = input("Enter Visitor ID: ")
                date = input("Enter Date of Visit (dd/mm/yyyy): ")
                rating = input("Enter Rating (1-10, or leave blank): ").strip()
                rating = int(rating) if rating.isdigit() else None
                manager.add_visit(visitor_id, poi_id, date, rating)

            elif choice == '7':
                type_name = input("Enter POI Type Name to delete: ")
                manager.delete_poi_type(type_name)

            # --- POI QUERIES (PQ) ---
            elif choice == '8':
                type_name = input("Enter POI Type Name: ")
                result = manager.query_pq1_list_by_type(type_name)
                print(f"\n--- POIs of Type: {type_name} ({len(result)} found) ---")
                for item in result:
                    print(f"ID: {item['id']}, Name: {item['name']}, Loc: {item['location']}, Attrs: {item['attributes']}")

            elif choice == '9':
                result = manager.query_pq2_closest_pair()
                print("\n--- Closest Pair of POIs ---")
                if result:
                    dist, (p1, p2) = result
                    print(f"Distance: {dist:.4f}")
                    print(f"POI 1: ID {p1.id}, Name: {p1.name}, Location: {p1.location}")
                    print(f"POI 2: ID {p2.id}, Name: {p2.name}, Location: {p2.location}")
                else:
                    print("Need at least 2 POIs to find a closest pair.")
            
            elif choice == '10':
                result = manager.query_pq3_count_by_type()
                print("\n--- POI Count Per Type ---")
                for type_name, count in result:
                    print(f"Type: {type_name.ljust(15)} | Count: {count}")

            elif choice == '11':
                x = int(input("Enter Center X: "))
                y = int(input("Enter Center Y: "))
                r = float(input("Enter Radius r: "))
                result = manager.query_pq4_within_radius((x, y), r)
                print(f"\n--- POIs Within Radius {r} of ({x}, {y}) ({len(result)} found) ---")
                for item in result:
                    print(f"ID: {item['id']}, Name: {item['name']}, Dist: {item['distance']:.4f}, Type: {item['type']}")

            elif choice == '12':
                x = int(input("Enter Center X: "))
                y = int(input("Enter Center Y: "))
                k = int(input("Enter K (number of nearest POIs): "))
                result = manager.query_pq5_k_nearest((x, y), k)
                print(f"\n--- {k} Nearest POIs to ({x}, {y}) ---")
                for item in result:
                    print(f"ID: {item['id']}, Name: {item['name']}, Dist: {item['distance']:.4f}, Type: {item['type']}")

            elif choice == '13':
                x = int(input("Enter Center X: "))
                y = int(input("Enter Center Y: "))
                r = float(input("Enter Radius r (Boundary Check): "))
                result = manager.query_pq6_boundary_correctness((x, y), r)
                print(f"\n--- POIs Exactly At Distance {r} ({len(result)} found) ---")
                for item in result:
                    print(f"ID: {item['id']}, Name: {item['name']}, Dist: {item['distance']:.4f}, Type: {item['type']}")
            
            # --- VISITOR & POI QUERIES (VQ) ---
            elif choice == '14':
                visitor_id = input("Enter Visitor ID: ")
                result = manager.query_vq1_visitor_visits(visitor_id)
                print(f"\n--- Visited POIs for Visitor ID {visitor_id} ({len(result)} total visits) ---")
                for item in result:
                    print(f"POI ID: {item['poi_id']}, Name: {item['poi_name']}, Date: {item['date']}")
                
            elif choice == '15':
                result = manager.query_vq2_visitors_per_poi()
                print("\n--- Unique Visitor Count Per POI ---")
                for item in result:
                    print(f"POI ID: {item['poi_id']}, Name: {item['poi_name'].ljust(25)} | Unique Visitors: {item['visitor_count']}")

            elif choice == '16':
                result = manager.query_vq3_pois_per_visitor()
                print("\n--- Unique POI Count Per Visitor ---")
                for item in result:
                    print(f"Visitor: {item['visitor_name'].ljust(15)} | Unique POIs: {item['poi_count']}")

            elif choice == '17':
                k = int(input("Enter K (for top K visitors): "))
                result = manager.query_vq4_top_k_visitors(k)
                print(f"\n--- Top {k} Visitors by Unique POI Count ---")
                for item in result:
                    print(f"Count: {item['poi_count']}, Name: {item['visitor_name'].ljust(15)}, ID: {item['visitor_id'][:8]}...")
            
            elif choice == '18':
                k = int(input("Enter K (for top K POIs): "))
                result = manager.query_vq5_top_k_pois(k)
                print(f"\n--- Top {k} POIs by Unique Visitor Count ---")
                for item in result:
                    print(f"Count: {item['visitor_count']}, Name: {item['poi_name'].ljust(25)}, ID: {item['poi_id']}")

            elif choice == '19':
                m = int(input("Enter minimum number of unique POIs (m): "))
                t = int(input("Enter minimum number of distinct POI types (t): "))
                result = manager.query_vq7_coverage_fairness(m, t)
                print(f"\n--- Visitors Meeting Coverage Fairness (m={m}, t={t}) ({len(result)} found) ---")
                for item in result:
                    print(f"Name: {item['name'].ljust(15)} | Visited POIs: {item['total_pois_visited']}, Distinct Types: {item['num_distinct_poi_types']}")
            
            else:
                print("\n*** Invalid choice. Please enter a number from the menu. ***")

        except ValueError as e:
            print(f"\n*** Input Error (Make sure to enter numbers for IDs, coordinates, K, R): {e} ***")
        except Exception as e:
            print(f"\n*** System Error: {e} ***")

if __name__ == '__main__':
    main_cli()