"""Memory observer tests."""

import pytest
from ..observer_func.callb import Callb_store, Invoke_callb_store
from .dummies import Dummy_invokable_func, Dummy_observer_func


class Test_callb_store:
    """Callback storage and executor tests."""

    @pytest.fixture
    def fixt(self) -> Callb_store:
        return Callb_store()

    def test_add_and_run_callbs(self, fixt: Callb_store) -> None:
        """Run callbacks and checks if values are passed to proper callbacks."""
        avs = {19: 55, 20: 17, 21: 3}

        c1 = Dummy_observer_func([19, 45, 20, 21, 1], fixt)
        c2 = Dummy_observer_func([14, 19, 22], fixt)

        fixt.run_callbs(19, [avs[a] for a in [19, 20]])
        fixt.run_callbs(21, [avs[21]])

        assert c1.results[19] == avs[19]
        assert c1.results[20] == avs[20]
        assert c1.results[21] == avs[21]
        assert c1.results[1] == None
        assert c1.results[45] == None

        assert c2.results[19] == avs[19]
        assert c2.results[22] == None
        assert c2.results[14] == None


class Test_invoke_callb_store:
    """Callback storage and executor tests."""

    @pytest.fixture
    def fixt(self) -> Invoke_callb_store:
        return Invoke_callb_store()

    def test_add_and_run_callbs(self, fixt: Invoke_callb_store) -> None:
        c1 = Dummy_invokable_func(fixt)
        c2 = Dummy_invokable_func(fixt)

        fixt.run_callbs()

        assert c1.result
        assert c2.result
