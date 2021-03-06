""" Several methods that train a neural network given a training dataset. """

import numpy as np
from collections import deque
from util import unroll_matrices, reshape_vector

def train(nnet, X, y, learn_rate, errfn, minimizer, iterations = 10):
  """ Trains the neural network using the passed parameters.

  This method will train a neural network based on several parameters which will be used to setup
  the cost function. It will attempt to train the neural network by minimizing the cost function
  using the specified minimizer.

  A minimizer should be a function that takes two arguments:
  1) A function to minimize - This function will take a numpy.array of arguments and output the
    value of the function as well as the gradient of the function.
  2) The initial input values - A initial array of values to start the minimization process.

  The minimizer will be passed these arguments within this method, and is expected to return a
  results object that contains:
  1) success (bool) - whether the minimization was successful
  2) x (array) - the final minimized coordinate as a numpy.array
  3) fun (float) - the final minimized value of the function

  The minimizer follows the standard in scipy.optimize, so it is expected that an minimization
  function be chosen from that package.

  Arguments:
  X -- The featureset with each column representing a feature vector for one training example.
  y -- The output vector with each column representing the output vector for one training example.
  learn_rate -- The learning rate for regularization
  errfn -- Error function used when computing cost
  minimizer -- A minimization function
  iterations -- Number of times to attempt to minimize the cost with different starting weights;
    the weights and the result with the lowest cost will be picked (Default: 10)
  Returns:
  The result object returned from minimizer. The neural network passed will be mutated (trained)
  after this function is run.
  """
  costfn = create_costfn(nnet, X, y, learn_rate, errfn)
  dimensions = nnet.dimensions
  def flattened_costfn(weights):
    """ Wrapper function that flattens inputs to pass to a minimizer.

    Will return the gradient as a unrolled numpy.array.

    Arguments:
    weights -- a row vector of weights
    Returns:
    The cost and the gradient of the neural network given the weights.
    """
    cost, grad = costfn(reshape_vector(np.matrix(weights), dimensions))
    return cost, np.array(unroll_matrices(grad).T)[0]

  best_result = None
  min_error = float('infinity')
  for i in xrange(iterations):
    nnet.resetWeights()
    initial_weights = np.array(unroll_matrices(nnet.weights).T)[0]
    result = minimizer(flattened_costfn, initial_weights)
    if result.success and result.fun < min_error:
      best_result = result
      min_error = result.fun

  if best_result is not None:
    min_weights = reshape_vector(np.matrix(best_result.x), dimensions)
    nnet.weights = min_weights

  return best_result

def create_costfn(nnet, X, y, learn_rate, errfn, computeGrad=True):
  """ Creates a cost function given a set of input data and other parameters.

  This method uses the provided dataset and other parameters to create a cost function that will
  calculate both a cost and a gradient.

  Arguments:
  X -- The featureset with each column representing a feature vector for one training example.
  y -- The output vector with each column representing the output vector for one training example.
  learn_rate -- The learning rate for regularization
  errfn -- Error function used when computing cost
  computeGrad -- Whether or not to compute the gradient or not in addition to the cost
  Returns:
  A cost function that takes a list of weights.

  Note: The number of columns in X and y represent the number of training examples, so the number
  of columns of each must match up. Otherwise, a matrix dimension mismatch error will be raised.
  """
  learn_rate = float(learn_rate)

  def costfn(weights):
    """ The cost function created which calculates the cost of using a particular list of weights.

    Uses the parameters passed to createCostfn to calculate the cost and the gradient given a list
    of weights. The weights should be correctly shaped.

    The cost is calculated by running forward propogation on the neural network and calculating
    the error between the output and the expected values. The gradient of the cost is calculated
    using backpropogation, utilizing the grad function in each of the activation functions and the
    error function. The cost function utilizes regularization which can be tuned by the learn_rate
    parameter in createCostfn.

    The cost function depends on all the inputs passed to createCostfn, so tweaking the parameters
    to createCostfn will change the behavior of the cost function.

    Arguments:
    weights -- A list of weights
    Returns:
    The cost and, if computeGrad is True, the gradient of the neural network.
    """
    try:
      # Set the weights of the neural network
      nnet.weights = weights

      # Helper variables
      m = float(X.shape[1]) # Number of training examples
      bias = 1 if nnet.bias else 0

      # Part 1: Feed forward and get cost
      z, a, cost = nnet.calculateCost(X, y, errfn, learn_rate)
      h = a[-1] # Hypothesis

      if computeGrad:
        # Part 2: Backpropogation and get grad
        d = deque()

        # Calculate deltas
        d.appendleft(np.multiply(nnet.layers[-1].activationfn.grad(z[-1]), errfn.grad(h, y)))

        for i in xrange(len(nnet.layers) - 2, 0, -1):
          prevD = d[0]
          activationfn = nnet.layers[i].activationfn
          weight = weights[i]
          d.appendleft(np.multiply(activationfn.grad(z[i]), weight[:, bias:].T * prevD))

        d.appendleft(None) # Filler since d0 is unimportant

        # Calculate gradients
        grads = list()
        for i in xrange(len(nnet.weights)):
          # Unregularized gradient
          unreg_grad = (1. / m) * d[i+1] * a[i].T
          # Regularized gradient excluding bias
          reg_grad = (learn_rate / m) * weights[i][:, bias:]
          # Create gradient
          grad = unreg_grad
          grad[:, bias:] += reg_grad
          grads.append(grad)

        return cost, grads
      else:
        return cost
    except ValueError:
      print "Calculating cost of a neural network failed. Most likely due to dimension mismatch."
      raise
  return costfn
