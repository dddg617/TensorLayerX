#! /usr/bin/python
# -*- coding: utf-8 -*-

import tensorlayerx as tlx
from tensorlayerx import logging
from tensorlayerx.nn.core import Module

__all__ = [
    'BinaryLinear',
]


class BinaryLinear(Module):
    """The :class:`BinaryLinear` class is a binary fully connected layer, which weights are either -1 or 1 while inferencing.

    Note that, the bias vector would not be binarized.

    Parameters
    ----------
    out_features : int
        The number of units of this layer.
    act : activation function
        The activation function of this layer, usually set to ``tf.act.sign`` or apply :class:`Sign` after :class:`BatchNorm`.
    use_gemm : boolean
        If True, use gemm instead of ``tf.matmul`` for inference. (TODO).
    W_init : initializer or str
        The initializer for the weight matrix.
    b_init : initializer or None or str
        The initializer for the bias vector. If None, skip biases.
    in_features: int
        The number of channels of the previous layer.
        If None, it will be automatically detected when the layer is forwarded for the first time.
    name : None or str
        A unique layer name.

    Examples
    --------
    >>> net = tlx.nn.Input([10, 784], name='input')
    >>> net = tlx.nn.BinaryLinear(out_features=800, act=tlx.ReLU, name='BinaryLinear1')(net)
    >>> output shape :(10, 800)
    >>> net = tlx.nn.BinaryLinear(out_features=10, name='BinaryLineart')(net)
    >>> output shape : (10, 10)

    """

    def __init__(
        self,
        out_features=100,
        act=None,
        use_gemm=False,
        W_init='truncated_normal',
        b_init='constant',
        in_features=None,
        name=None,
    ):
        super().__init__(name, act=act)
        self.out_features = out_features
        self.use_gemm = use_gemm
        self.W_init = self.str_to_init(W_init)
        self.b_init = self.str_to_init(b_init)
        self.in_features = in_features

        if self.in_features is not None:
            self.build((None, self.in_features))
            self._built = True

        logging.info(
            "BinaryDense  %s: %d %s" %
            (self.name, out_features, self.act.__class__.__name__ if self.act is not None else 'No Activation')
        )

    def __repr__(self):
        actstr = self.act.__class__.__name__ if self.act is not None else 'No Activation'
        s = ('{classname}(out_features={out_features}, ' + actstr)
        if self.in_features is not None:
            s += ', in_features=\'{in_features}\''
        if self.name is not None:
            s += ', name=\'{name}\''
        s += ')'
        return s.format(classname=self.__class__.__name__, **self.__dict__)

    def build(self, inputs_shape):
        if len(inputs_shape) != 2:
            raise Exception("The input dimension must be rank 2, please reshape or flatten it")

        if self.in_features is None:
            self.in_features = inputs_shape[1]

        if self.use_gemm:
            raise Exception("TODO. The current version use tf.matmul for inferencing.")

        n_in = inputs_shape[-1]
        self.W = self._get_weights("weights", shape=(n_in, self.out_features), init=self.W_init)
        self.b = None
        if self.b_init is not None:
            self.b = self._get_weights("biases", shape=(self.out_features), init=self.b_init)
            self.bias_add = tlx.ops.BiasAdd()

        self.binary_dense = tlx.ops.BinaryDense(self.W, self.b)

    def forward(self, inputs):
        if self._forward_state == False:
            if self._built == False:
                self.build(tlx.get_tensor_shape(inputs))
                self._built = True
            self._forward_state = True

        outputs = self.binary_dense(inputs)

        if self.act:
            outputs = self.act(outputs)

        if not self._nodes_fixed and self._build_graph:
            self._add_node(inputs, outputs)
            self._nodes_fixed = True
        return outputs
