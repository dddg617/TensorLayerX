#! /usr/bin/python
# -*- coding: utf-8 -*-

import tensorlayerx as tl
from tensorlayerx import logging
from tensorlayerx.core import Module

__all__ = [
    'TernaryDense',
]


class TernaryDense(Module):
    """The :class:`TernaryDense` class is a ternary fully connected layer, which weights are either -1 or 1 or 0 while inference.
    # TODO The TernaryDense only supports TensorFlow backend.

    Note that, the bias vector would not be tenaried.

    Parameters
    ----------
    n_units : int
        The number of units of this layer.
    act : activation function
        The activation function of this layer, usually set to ``tf.act.sign`` or apply :class:`SignLayer` after :class:`BatchNormLayer`.
    use_gemm : boolean
        If True, use gemm instead of ``tf.matmul`` for inference. (TODO).
    W_init : initializer or str
        The initializer for the weight matrix.
    b_init : initializer or None or str
        The initializer for the bias vector. If None, skip biases.
    in_channels: int
        The number of channels of the previous layer.
        If None, it will be automatically detected when the layer is forwarded for the first time.
    name : None or str
        A unique layer name.

    """

    def __init__(
        self,
        n_units=100,
        act=None,
        use_gemm=False,
        W_init='truncated_normal',
        b_init='constant',
        in_channels=None,
        name=None,  #'ternary_dense',
    ):
        super().__init__(name, act=act)
        self.n_units = n_units
        self.use_gemm = use_gemm
        self.W_init = self.str_to_init(W_init)
        self.b_init = self.str_to_init(b_init)
        self.in_channels = in_channels

        if self.in_channels is not None:
            self.build((None, self.in_channels))
            self._built = True

        logging.info(
            "TernaryDense  %s: %d %s" %
            (self.name, n_units, self.act.__class__.__name__ if self.act is not None else 'No Activation')
        )

    def __repr__(self):
        actstr = self.act.__name__ if self.act is not None else 'No Activation'
        s = ('{classname}(n_units={n_units}, ' + actstr)
        if self.in_channels is not None:
            s += ', in_channels=\'{in_channels}\''
        if self.name is not None:
            s += ', name=\'{name}\''
        s += ')'
        return s.format(classname=self.__class__.__name__, **self.__dict__)

    def build(self, inputs_shape):
        if len(inputs_shape) != 2:
            raise Exception("The input dimension must be rank 2, please reshape or flatten it")

        if self.in_channels is None:
            self.in_channels = inputs_shape[1]

        if self.use_gemm:
            raise Exception("TODO. The current version use tf.matmul for inferencing.")

        n_in = inputs_shape[-1]

        self.W = self._get_weights(var_name="weights", shape=(n_in, self.n_units), init=self.W_init)
        self.b = None
        if self.b_init is not None:
            self.b = self._get_weights(var_name="biases", shape=(self.n_units), init=self.b_init)
        self.ternary_dense = tl.ops.TernaryDense(self.W, self.b)

    def forward(self, inputs):
        if self._forward_state == False:
            if self._built == False:
                self.build(tl.get_tensor_shape(inputs))
                self._built = True
            self._forward_state = True
        outputs = self.ternary_dense(inputs)
        if self.act:
            outputs = self.act(outputs)
        return outputs
