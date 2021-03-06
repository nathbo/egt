"""I really want to clean up my script

Passing kwargs and parameters around leads to quite some errors.
"""
import numpy as np
import logging
import tqdm


def minimize(f, J_class, initial_population, U, parameters):
    """Run the WHOLE simulation


    Parameters
    ----------
    f : function
        Function to minimize
    J_class : subclass of egt.game_template.J_template
        The game J to use for minimization
    initial_population : tuple
        Tuple of (locations, strategies) describing the starting population
    U : np.array
        Set of available strategies for the individuals
    """
    # 1. Init
    #   Initialize population, strategies, parameters
    # 2. Run the iteration, consisting of
    #   a. Strategy updates: replicator dynamics
    #   b. Location updates
    beta = parameters['beta']
    gamma = parameters['gamma']
    stepsize = parameters['stepsize']
    max_iterations = parameters['max_iterations']
    s_rounds = parameters['s_rounds']
    normalize_delta = parameters['normalize_delta']
    smooth_movement = parameters['smooth_movement']
    epsilon = parameters['epsilon']

    standing_index = np.where(np.isclose(U, 0))[0][0]

    J_vectorized = J_class.get(f, U, epsilon=epsilon)

    locations, strategies = initial_population
    N, d = locations.shape

    ###########################################################################
    # Define Magnet and Replicator Dynamics
    ###########################################################################
    def magnet(locations):
        """Reweighting, so that "good" points are more important in comparison

        w_i = e^{beta*(f(x_i) - min_k f(x_k))}
        """
        # Reweighting
        f_vals = f(locations).flatten()
        f_min = f_vals.min()
        weights = np.exp(-beta*(f_vals - f_min))
        weights /= np.sum(weights)
        logging.debug(np.sort(weights))
        return weights

    def replicator_dynamics(current_population):
        locations, strategies = current_population
        N, d = locations.shape

        tot_J = J_vectorized(locations)

        weights = magnet(locations)

        mean_outcomes = np.sum(tot_J * strategies[:, None, :], axis=2)
        delta = np.sum(
            weights[None, :, None] * (
                tot_J - mean_outcomes[:, :, None]),
            axis=1)

        return delta

    ###########################################################################
    # Start the iterative part here
    ###########################################################################

    history = []
    history.append((locations.copy(), strategies.copy()))

    logging.info('Start simulation')
    sim_bar = tqdm.trange(max_iterations)
    try:
        for i in sim_bar:
            # Strategy updates
            for s in range(s_rounds):
                # Formula: sigma = (1 + stepsize * gamma * delta) * sigma

                # All possible calls of J, in a single array, but without the diag
                delta = replicator_dynamics((locations, strategies))

                if normalize_delta:
                    delta = - delta / delta.min(axis=1)[:, None]

                strategies *= (1 + stepsize * gamma * delta)
                # import pdb; pdb.set_trace()

                prob_sums = strategies.sum(axis=1)
                if np.any(prob_sums != 1) and np.all(np.isclose(prob_sums, 1)):
                    # Numerical problems, but otherwise should be fine - Reweight
                    strategies /= prob_sums[:, None]

            # Location updates
            for j in range(N):
                if smooth_movement:
                    locations[j] += strategies[j].flatten().dot(U)
                else:
                    random_u_index = np.random.choice(
                        len(U), p=strategies[j].flatten())
                    locations[j] += stepsize*U[random_u_index]

            if i % 10 == 9:
                history.append((locations.copy(), strategies.copy()))

            # Break condition for early stopping
            max_dist = (max(locations) - min(locations))[0]
            max_staying_uncertainty = 1 - strategies[:, standing_index].min()
            mean_value = np.mean(f(locations))
            min_location = np.min(locations)
            max_location = np.max(locations)
            sim_bar.set_description(
                ('[Simulation] max_dist={:.3f} ' +
                 'max_uncert={:.2E} ' +
                 'min_loc={:.2f} ' +
                 'max_loc={:.2f} ' +
                 'mean_value={:.2f}').format(
                    max_dist,
                    max_staying_uncertainty,
                    min_location,
                    max_location,
                    mean_value))
            # if max_staying_uncertainty == 0.0:
            if max_staying_uncertainty < 1e-8:   # Gotta go fast
                logging.info('Early stopping! No point wants to move anymore')
                break
            if max_dist <= np.abs(U[standing_index+1]):
                logging.info('Early stopping! Points are VERY close')
                break
    except KeyboardInterrupt:
        print('Breaking the simulation. If you really want to exit press it again in the next 5 seconds')
        import time
        time.sleep(5)

    logging.info(f'Max distance at the end: {max_dist}')
    logging.info(f'Max "staying-uncertainty": {max_staying_uncertainty}')

    return history
