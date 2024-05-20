import numpy as np
import xarray as xr

from metpy.units import units

def smooth_temperature_xarray(temperature: xr.DataArray, weights: list,
                              keep_all_days=False) -> xr.DataArray:
    """
    Smooth a temperature DataArray over the 'step' dimension with the given weighting for previous steps.
    
    Validated against the original pandas implementation, witht the only difference in how the weights are supplied (the weight for the current step is included in the list in this implementation, whereas it is not in the pandas implementation)

    Params
    ------
    temperature : xr.DataArray
    weights : list
        The weights for smoothing, in reverse chronological order (most recent first).
        The first element is the weight for the current step, the second element is for the previous step, etc.
    keep_all_days : bool
    """
    # Reverse the weights to chronological order and ensure the current day's weight is included
    weights = weights[::-1]
    
    
    # Create a DataArray for the weights with the 'step' dimension
    weights_da = xr.DataArray(weights, dims=['window'])
    fill_value = np.nan
    if keep_all_days: 
        # assert no prior nans 
        assert temperature.isnull().sum() == 0
        fill_value = 0
    
    # Use the rolling window to apply the weights
    # The construct method aligns the weights correctly with the window
    smoothed = (
        temperature.rolling(step=len(weights), min_periods=1)
        .construct('window')
        .fillna(fill_value)
        .dot(weights_da, dims=['window'])
    )
    # Normalize by the sum of weights
    total_weights_sum = weights_da.sum()
    # If we're keeping all days, we need to adjust the normalization for the first few steps
    if keep_all_days:
        # unfinished, fail if invoked
        # raise NotImplementedError
        # Initialize an array to hold the normalization factors
        normalization_factors = xr.full_like(smoothed, total_weights_sum)
        
        # Adjust the normalization factors for each step
        for i in range(len(weights)):
            # Calculate the sum of weights for the truncated window
            truncated_weights_sum = np.sum(weights[-(i+1):])
            normalization_factors[:i+1] = truncated_weights_sum

        # Apply the normalization factors to the smoothed data
        smoothed = smoothed / normalization_factors
    else:
        smoothed = smoothed / total_weights_sum

    return smoothed


def get_hdd(temperature: xr.DataArray, threshold: float) -> xr.DataArray:
    """
    Calculate Heating Degree Days (HDD) for an xarray DataArray of temperatures.

    Params
    ------
    temperature : xr.DataArray
        The temperatures for each step.
    threshold : float
        The base temperature below which heating is required.

    Returns
    -------
    hdd : xr.DataArray
        Heating Degree Days for each step.
    """
    # Calculate HDD by subtracting the temperature from the threshold,
    # and clipping the result at a minimum of 0
    hdd = xr.where(temperature < threshold, threshold - temperature, 0)
    return hdd

def get_cdd(temperature: xr.DataArray, threshold: float) -> xr.DataArray:
    """
    Calculate Cooling Degree Days (CDD) for an xarray DataArray of temperatures.

    Params
    ------
    temperature : xr.DataArray
        The temperatures for each step.
    threshold : float
        The base temperature above which cooling is required.

    Returns
    -------
    cdd : xr.DataArray
        Cooling Degree Days for each step.
    """
    # Calculate CDD by subtracting the threshold from the temperature,
    # and clipping the result at a minimum of 0
    cdd = xr.where(temperature > threshold, temperature - threshold, 0)
    return cdd

def _bait_xarray(
    weather: xr.Dataset,
    smoothing: float,
    solar_gains: float,
    wind_chill: float,
    humidity_discomfort: float,
) -> xr.DataArray:
    """
    Calculate the 'feels like' temperature index (BAIT) using an xarray Dataset.

    Params
    ------
    weather : xr.Dataset
        Must contain 'humidity', 'radiation_global_horizontal', 'temperature',
        and 'wind_speed_2m' data variables.

    smoothing, solar_gains, wind_chill, humidity_discomfort : float
        Parameters for calculating the BAIT.
    """
    T = weather["temperature"]
    setpoint_S = 100 + 7 * T  # W/m2
    setpoint_W = 4.5 - 0.025 * T  # m/s
    setpoint_H = np.exp(1.1 + 0.06 * T)/1000  # kg water per kg air
    setpoint_T = 16  # degrees C - around which 'discomfort' is measured

    # Calculate the unsmoothed ninja temperature index
    N = (weather["temperature"].copy()
        + (weather["radiation_global_horizontal"] - setpoint_S) * solar_gains
        + (weather["wind_speed_2m"] - setpoint_W) * wind_chill)

    # If it's sunny, it feels warmer
    # If it's windy, it feels colder
    # If it's humid, both hot and cold feel more extreme
    discomfort = N - setpoint_T
    N = (
        setpoint_T
        + discomfort
        + (
            discomfort
            #* ((weather["humidity"] / 1000) - setpoint_H)
            # converted to kg/kg from g/kg #TODO possible error in the original code?
            * ((weather["humidity"]) - setpoint_H)
            * humidity_discomfort
        )
    )

    # Apply temporal smoothing to our temperatures over the last two days
    # N = smooth_temperature_xarray(N, weights=[smoothing**(i/4) for i in range(0, 12)])
    N = smooth_temperature_xarray(N, weights=[1]*4+[smoothing]*4+[smoothing**2]*4)

    # Blend the smoothed BAIT with raw temperatures
    lower_blend = 15  # *C at which we start blending T into N
    upper_blend = 23  # *C at which we have fully blended T into N
    max_raw_var = 0.5  # maximum amount of T that gets blended into N

    # Transform this window to a sigmoid function, mapping lower & upper onto -5 and +5
    avg_blend = (lower_blend + upper_blend) / 2
    dif_blend = upper_blend - lower_blend
    blend = (weather["temperature"] - avg_blend) * 10 / dif_blend
    blend = max_raw_var / (1 + np.exp(-blend))

    # Apply the blend
    N = (weather["temperature"] * blend) + (N * (1 - blend))

    N.attrs['long_name'] = 'Building-Adjusted Internal Temperature'
    N.attrs['short_name'] = 'BAIT'
    N.attrs['units'] = 'degC'  # Assuming the temperature is in degrees Celsius
    
    return N