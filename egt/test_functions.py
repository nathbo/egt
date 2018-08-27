import numpy as np
from scipy.signal import argrelextrema
import logging


def ackley(x):
    out = -20 * np.exp(-0.2 * np.sqrt(0.5 * (x**2))) - np.exp(
        0.5 * (np.cos(2 * np.pi * x) + 1)) + np.exp(1) + 20
    return out


def simple_nonconvex_function(x):
    return (x**2) - 0.8 * np.cos(30*x)


def two_wells(x):
    return (((x-2)**2 * (x+2)**2 + 10*x) / (x**2 + 1) +
            0.3 * (np.abs(x)+5) * np.sin(10*x))


def convex_hull(f, plot_range=np.arange(-100, 100, 0.001)):
    if f == simple_nonconvex_function:
        return lambda x: x**2 - 0.8

    logging.info('Creating convex hull - can take a while')
    out_function = two_wells

    def step(previous_function,
             local_minima_index,
             local_minima_location,
             local_minima_value):
        # Closure to keep the namespace for the new function each iteration
        def new_function(x):
            if np.any(local_minima_location == x):
                return local_minima_value[local_minima_location == x]

            if (np.all(local_minima_location <= x) or
                    np.all(local_minima_location >= x)):
                return previous_function(x)
            right_min_index = (local_minima_location > x).argmax()
            left_min_index = right_min_index - 1
            left_min = local_minima_location[left_min_index]
            right_min = local_minima_location[right_min_index]
            left_min_val = previous_function(left_min)
            right_min_val = previous_function(right_min)

            out = ((left_min_val * (right_min - x) +
                    right_min_val * (x - left_min)) /
                   (right_min - left_min))

            return out
        return new_function

    while True:
        f_vals = np.array([out_function(x) for x in plot_range])
        local_minima_index = argrelextrema(f_vals, np.less)[0]
        if len(local_minima_index) == 1:
            # We're finished, one local min means it is convex!
            break
        local_minima_location = plot_range[local_minima_index]
        local_minima_value = f_vals[local_minima_index]

        out_function = step(
            out_function,
            local_minima_index,
            local_minima_location,
            local_minima_value)

    # Enable it to use arrays naively
    def array_function(x):
        if isinstance(x, np.ndarray):
            assert len(x) == x.shape[0]
            return [out_function(entry) for entry in x]
        else:
            return out_function(x)

    return array_function


def easom(x):
    return np.cos(x) * np.exp(-((x-np.pi)**2))