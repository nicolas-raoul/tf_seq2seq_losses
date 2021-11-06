import os
import unittest
import tensorflow as tf
import numpy as np

from tf_seq2seq_losses.tools import logsumexp, insert_zeros, unsorted_segment_logsumexp, finite_difference_gradient, \
    unfold


os.environ["CUDA_VISIBLE_DEVICES"] = ""


class TestLogSumExp(unittest.TestCase):
    def test_basic(self):
        x = tf.constant([-3.0753517, -np.inf, -np.inf])
        y = tf.constant([-1.000000e+12, -4.283799e-01, -np.inf])

        output = logsumexp(x=x, y=y)

        self.assertAlmostEqual(max(np.abs(np.array([-3.0753517, -0.4283799, -np.inf]) - output.numpy())), 0, 6)


class TestInsert(unittest.TestCase):
    def test_example(self):
        output = insert_zeros(
            tensor=tf.constant(
               [[1, 2, 3, 4, 5],
                [10, 20, 30, 40, 50]],
            dtype=tf.int32),
            mask=tf.constant(
               [[False, True, False, False, True],
                [False, True,  True, True,  False]]
            ),
        )

        self.assertEqual(
            [[1, 0, 2, 3, 4, 0, 5, 0],
             [10, 0, 20, 0, 30, 0, 40, 50]],
            output.numpy().tolist()
        )

    def test_basic(self):
        output = insert_zeros(
            tensor=tf.constant(
               [[1, 2, 2, 0, 0],
                [1, 1, 1, 1, 0]],
            dtype=tf.int32),
            mask=tf.constant(
               [[False, False, True, False, True],
                [False, True,  True, True,  False]]
            ),
        )

        self.assertEqual(
            [[1, 2, 0, 2, 0, 0, 0, 0],
             [1, 0, 1, 0, 1, 0, 1, 0]],
            output.numpy().tolist()
        )


class TestFiniteDifferenceDerivative(unittest.TestCase):
    def test_basic(self):
        def func(x: tf.Tensor) -> tf.Tensor:
            return tf.reduce_sum(x ** 2, axis=[1, 2]) / 2
        x = tf.ones(shape=[2, 3, 4])

        derivative = finite_difference_gradient(func=func, x=x, epsilon=1e-3)

        expected_derivative = tf.ones(shape=[2, 3, 4], dtype=tf.float32)
        self.assertLess(tf.reduce_max(tf.abs(derivative - expected_derivative)), 1e-3)


class TestUnsortedSegmentLogsumexp(unittest.TestCase):
    def test_shape(self):
        data = tf.ones(shape=[3, 4, 5, 6])
        segment_ids = tf.constant([[0, 1, 0, 1], [0, 1, 0, 1], [0, 1, 0, 1]])
        num_segments = 2

        output = unsorted_segment_logsumexp(data=data, segment_ids=segment_ids, num_segments=num_segments)

        self.assertEqual((2, 5, 6), output.shape)

    def test_basic(self):
        data = tf.constant([0, -np.inf, 0, -np.inf])
        segment_ids = tf.constant([0, 1, 0, 1])
        num_segments = 2

        output = unsorted_segment_logsumexp(data=data, segment_ids=segment_ids, num_segments=num_segments)

        self.assertAlmostEqual(np.log(2), output.numpy()[0], 8)
        self.assertEqual(-np.inf, output.numpy()[1])


class TestUnfold(unittest.TestCase):
    def test_doc_example(self):
        output = unfold(
            init_tensor=tf.constant(0, dtype=tf.int32),
            iterfunc=lambda x, i: x + i,
            num_iters=5,
            d_i=1,
            element_shape=tf.TensorShape([]),
        )

        self.assertEqual([0, 0, 1, 3, 6, 10], output.numpy().tolist())