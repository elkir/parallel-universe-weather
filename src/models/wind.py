import xarray as xr
import numpy as np



bounds_wpp_diff = np.linspace(-1e4,1e4,1001)


def calculate_wind_power_potential(da_wind, hub_height=None, alpha=1/7,
                                   cap_speed=11.0,
                                   cut_out_speed=25.0,
                                   cut_in_speed=3.0,
                                   wind_speed_name='w100'):
    """
    Calculate the wind power potential field from wind speed data at different heights.

    Parameters:
    - ds: xarray.Dataset or xarray.DataArray containing wind speed data [m/s] at 100m
    - hub_height: The height of the wind turbine hub.
    - cut_out_speed: The cut-out speed of the wind turbine.
    - alpha: Hellmann exponent (default is 1/7, typical for neutral atmospheric conditions over open land).

    Returns:
    - xarray.DataArray containing the estimated wind power potential.
    """
    
    # Constants
    air_density = 1.225  # kg/m^3, at sea level and 15°C
    
    if isinstance(da_wind, xr.Dataset):
        da_wind = da_wind[wind_speed_name]
    
    
    # Calculate the wind speed at the hub height using the power law

    # only do this if we;re not already at 100m
    if hub_height is not None and hub_height != 100.0:
        da_wind = da_wind * (hub_height / 100.0) ** alpha

    
     # Set wind speed to zero if it exceeds the cut-out speed
    da_wind = da_wind.where(da_wind <= cut_out_speed, other=0)
    da_wind = da_wind.where(da_wind >= cut_in_speed, other=0)
    da_wind = da_wind.where(da_wind <= cap_speed, other=cap_speed)
    
    # Calculate the wind power density
    wind_power_density = 0.5 * air_density * da_wind ** 3
    
    # ### ^^^^ faster then this vvvv ###
    # ##################################
    # mask_cubical_increase = (da_wind >= cut_in_speed) & (da_wind < cap_speed)
    # mask_max_power = (da_wind >= cap_speed) & (da_wind <= cut_out_speed)
    # max_power = 0.5 * air_density * cap_speed ** 3
    # wind_power_density=(0.5*air_density*da_wind.where(mask_cubical_increase)**3).fillna(0) +mask_max_power*max_power
    # ##################################
    
    
    
    
    
    if hub_height is not None:
        description=  f'Wind power density at {hub_height}m calculated from wind speed at 100m using the power law'
    else :
        description=  f'Wind power density at 100m'
    # assign attributes
    wind_power_density.attrs = {
        'long_name': 'Wind power density',
        'units': 'W m**-2',
        'description': description
    }
    
    return wind_power_density
