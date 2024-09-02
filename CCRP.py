import numpy as np
import mgrs
import utm

# Constants and Payload Factors
G = 9.81  # Gravity
C_d = 0.005  # Drag coefficient
rho = 1.225  # Air density (kg/m^3)
A = 0.1  # Cross-sectional area of the bomb (m^2)
m = 250  # Mass of the bomb (kg)

# Aircraft Parameters
target_mgrs = "33TWN0000000000"  # Target MGRS coordinate
aircraft_mgrs = "33TWN0100000000"  # Aircraft MGRS coordinate
aircraft_speed = 250  # Aircraft speed (m/s)
aircraft_altitude = 5000  # Aircraft altitude (m)
dive_angle = np.radians(30)  # Dive angle (radians)
heading_angle = np.radians(0)  # Heading angle (radians)
wind = (10, 5, 0)  # Wind components (m/s)

# MGRS conversion object
mgrs_converter = mgrs.MGRS()

def mgrs_to_utm(mgrs_coord):
    """Convert MGRS to UTM."""
    latlon = mgrs_converter.toLatLon(mgrs_coord)
    return utm.from_latlon(latlon[0], latlon[1])

def utm_to_mgrs(easting, northing, zone_number, zone_letter):
    """Convert UTM to MGRS."""
    latlon = utm.to_latlon(easting, northing, zone_number, zone_letter)
    return mgrs_converter.toMGRS(latlon[0], latlon[1])

def compute_drag(v):
    return 0.5 * rho * C_d * A * v**2 / m

def bomb_trajectory(V, H, theta, phi, Wx, Wy, Wz, aircraft_pos, target_utm):
    """Calculate the bomb trajectory and time of flight."""
    Vx = V * np.cos(theta) * np.cos(phi)
    Vy = V * np.cos(theta) * np.sin(phi)
    Vz = -V * np.sin(theta)

    # Time integration to account for drag
    dt = 0.1  # Time step for integration
    t_flight = 0
    z = H
    x, y = 0, 0

    while z > 0:
        drag_x = compute_drag(Vx)
        drag_y = compute_drag(Vy)
        drag_z = compute_drag(Vz)
        
        Vx -= drag_x * dt
        Vy -= drag_y * dt
        Vz -= drag_z * dt
        z += Vz * dt
        
        x += Vx * dt + Wx * dt
        y += Vy * dt + Wy * dt
        t_flight += dt

    impact_easting = aircraft_pos[0] + x
    impact_northing = aircraft_pos[1] + y

    return impact_easting, impact_northing, t_flight

def ccrp_release_point(target_mgrs, V, H, theta, phi, wind=(0, 0, 0), aircraft_mgrs=None):
    """Calculate the release point MGRS, TTI, and TTR."""
    Wx, Wy, Wz = wind
    target_utm = mgrs_to_utm(target_mgrs)
    
    if aircraft_mgrs:
        aircraft_utm = mgrs_to_utm(aircraft_mgrs)
    else:
        aircraft_utm = target_utm

    impact_easting, impact_northing, t_flight = bomb_trajectory(V, H, theta, phi, Wx, Wy, Wz, aircraft_utm, target_utm)
    
    impact_mgrs = utm_to_mgrs(impact_easting, impact_northing, target_utm[2], target_utm[3])
    
    distance_to_release = np.sqrt((aircraft_utm[0] - impact_easting) ** 2 + (aircraft_utm[1] - impact_northing) ** 2)
    time_to_release = distance_to_release / V

    return impact_mgrs, t_flight, time_to_release

# Calculate RP
release_point_mgrs, tti, time_to_release = ccrp_release_point(
    target_mgrs, aircraft_speed, aircraft_altitude, dive_angle, heading_angle, wind, aircraft_mgrs
)

print(f"Release Point MGRS: {release_point_mgrs}")
print(f"Time to Impact (TTI): {tti:.2f} seconds")
print(f"Time to Release: {time_to_release:.2f} seconds")
