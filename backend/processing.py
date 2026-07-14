import math

def haversine_distance(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371000 
    return c * r

def process_severity(area_ratio, confidence):
    if area_ratio > 0.05:
        severity_score = 3
    elif area_ratio > 0.01:
        severity_score = 2
    else:
        severity_score = 1
        
    if confidence < 0.6 and severity_score > 1:
        severity_score -= 1
        
    if severity_score == 3:
        return 'severe'
    elif severity_score == 2:
        return 'moderate'
    else:
        return 'minor'

def find_duplicate_pothole(PotholeModel, db_session, lat, lon, distance_threshold=15.0):
    margin = 0.001
    candidates = db_session.query(PotholeModel).filter(
        PotholeModel.latitude.between(lat - margin, lat + margin),
        PotholeModel.longitude.between(lon - margin, lon + margin)
    ).all()
    
    for pothole in candidates:
        if haversine_distance(lat, lon, pothole.latitude, pothole.longitude) <= distance_threshold:
            return pothole
    return None
