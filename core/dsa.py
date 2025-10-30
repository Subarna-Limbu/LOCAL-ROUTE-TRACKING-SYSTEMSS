import heapq

def dijkstra(graph, start, end):
    """
    Compute the shortest path using Dijkstra's algorithm with heap optimization.
    
    Args:
        graph: dict, {node_id: [(neighbor_id, distance), ...]}
        start: starting node ID
        end: destination node ID
    
    Returns:
        tuple: (shortest_distance, path_list)
    """
    if start not in graph or end not in graph:
        return float('inf'), []
    
    if start == end:
        return 0, [start]
    
    # Initialize distances
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    
    # Track previous nodes for path reconstruction
    previous = {node: None for node in graph}
    
    # Priority queue: (distance, node)
    pq = [(0, start)]
    visited = set()
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current in visited:
            continue
        
        visited.add(current)
        
        # Found destination
        if current == end:
            break
        
        # Check neighbors
        for neighbor, weight in graph.get(current, []):
            distance = current_dist + weight
            
            if distance < distances.get(neighbor, float('inf')):
                distances[neighbor] = distance
                previous[neighbor] = current
                heapq.heappush(pq, (distance, neighbor))
    
    # Reconstruct path
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous.get(current)
    path.reverse()
    
    # Verify path is valid
    if path[0] != start:
        return float('inf'), []
    
    return distances[end], path


def is_route_valid(stops, pickup, destination):
    """
    Verify that the 'pickup' exists and is before 'destination' in the stop list.
    """
    if (pickup in stops) and (destination in stops) and (stops.index(pickup) < stops.index(destination)):
        return True
    return False


def find_best_route(all_routes, pickup_stop_id, dest_stop_id):
    """
    Find the route with shortest distance between pickup and destination.
    
    Args:
        all_routes: QuerySet of BusRoute objects
        pickup_stop_id: ID of pickup Stop
        dest_stop_id: ID of destination Stop
    
    Returns:
        tuple: (best_route, shortest_distance, path_stop_ids)
    """
    best_route = None
    best_distance = float('inf')
    best_path = []
    
    for route in all_routes:
        graph = route.get_stop_graph()
        
        # Check if both stops exist in this route
        if pickup_stop_id not in graph or dest_stop_id not in graph:
            continue
        
        distance, path = dijkstra(graph, pickup_stop_id, dest_stop_id)
        
        if distance < best_distance:
            best_distance = distance
            best_route = route
            best_path = path
    
    return best_route, best_distance, best_path