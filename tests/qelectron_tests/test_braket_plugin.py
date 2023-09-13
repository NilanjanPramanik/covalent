# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the GNU Affero General Public License 3.0 (the "License").
# A copy of the License may be obtained with this software package or at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html
#
# Use of this file is prohibited except in compliance with the License. Any
# modifications or derivative works of this file must retain this copyright
# notice, and modified files must contain a notice indicating that they have
# been altered from the originals.
#
# Covalent is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
#
# Relief from the License may be granted by purchasing a commercial license.

# pylint: disable=no-member

import pytest


def test_init_local_executor():
    """Test that the local Braket executor can be initialized."""

    import covalent as ct

    ct.executor.LocalBraketQubitExecutor()


def test_init_executor():
    """Test that the Braket executor can be initialized."""

    import covalent as ct

    ct.executor.BraketQubitExecutor()


def test_decorator_path():
    """Test that `ct.qelectron` is the QElectron decorator"""
    from typing import Callable

    import covalent as ct

    assert isinstance(ct.qelectron, Callable), f"`ct.qelectron` is a {type(ct.qelectron).__name__}"


def test_circuit_call_single():
    """Test calling a QNode vs. QElectron with a scalar argument."""

    import pennylane as qml
    from pennylane import numpy as np

    import covalent as ct

    executors = [
        ct.executor.LocalBraketQubitExecutor(shots=None, max_jobs=19),
        ct.executor.LocalBraketQubitExecutor(shots=10_000, max_jobs=1),
    ]

    @qml.qnode(qml.device("default.qubit", wires=2))
    def circuit(x):
        qml.RX(x, wires=0)
        qml.CNOT(wires=[0, 1])
        return qml.expval(qml.PauliZ(0))

    qe_circuit = ct.qelectron(circuit, executors=executors, selector="cyclic")

    x = np.array(0.5)

    # Ensure every QCluster member is used at least once.
    for _ in range(5):
        res_1 = circuit(x)
        res_2 = qe_circuit(x)

        assert isinstance(res_1, type(res_2))
        assert np.isclose(res_1, res_2, rtol=0.1)


def test_circuit_call_vector():
    """Test calling a QNode vs. QElectron with a vector argument."""

    import pennylane as qml
    from pennylane import numpy as np

    import covalent as ct

    executors = [
        ct.executor.LocalBraketQubitExecutor(shots=None, max_jobs=19),
        ct.executor.LocalBraketQubitExecutor(shots=10_000, max_jobs=1),
    ]

    @qml.qnode(qml.device("default.qubit", wires=2))
    def circuit(x):
        qml.RX(x, wires=0)
        qml.CNOT(wires=[0, 1])
        return qml.expval(qml.PauliZ(0))

    qe_circuit = ct.qelectron(circuit, executors=executors, selector="cyclic")

    X = np.random.rand(13) * 2 * np.pi

    # Ensure every QCluster member is used at least once.
    for _ in range(5):
        res_1 = circuit(X)
        res_2 = qe_circuit(X)

        assert isinstance(res_1, type(res_2))
        assert np.isclose(res_1, res_2, atol=0.2).all()


def test_grad_basic():
    """Test calling gradients QNode vs. QElectron."""

    import pennylane as qml
    from pennylane import numpy as np

    import covalent as ct

    executors = [
        ct.executor.LocalBraketQubitExecutor(shots=10_000, max_jobs=1),
        ct.executor.LocalBraketQubitExecutor(shots=None, max_jobs=19),
    ]

    @qml.qnode(qml.device("default.qubit", wires=2))
    def circuit(x):
        qml.RX(x, wires=0)
        qml.CNOT(wires=[0, 1])
        return qml.expval(qml.PauliZ(0))

    qe_circuit = ct.qelectron(circuit, executors=executors, selector="cyclic")

    x = np.array(0.5, requires_grad=True)

    # Ensure every QCluster member is used at least once.
    for _ in range(5):
        res_1 = qml.grad(circuit)(x)
        res_2 = qml.grad(qe_circuit)(x)

        with pytest.raises(AssertionError):
            # NOTE: expected to fail due to QElectron fast-gradients trickery.
            # NOTE: return types are QML tensor vs NumPy array, respectively.
            assert isinstance(res_1, type(res_2))

        assert np.isclose(res_1, res_2, rtol=0.1)