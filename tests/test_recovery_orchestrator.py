from unittest.mock import MagicMock
from graph_heal.recovery_system import EnhancedRecoverySystem, RecoveryActionType, RecoveryAction
from graph_heal.graph_analysis import ServiceGraph
from datetime import datetime


def test_rollback_on_partial_failure():
    sg = ServiceGraph()
    docker = MagicMock()
    ers = EnhancedRecoverySystem(sg, docker)

    # create action that will fail first but succeed on rollback
    fail_action = ers.create_recovery_action("svc", RecoveryActionType.RESTART)
    rollback_action = ers.create_recovery_action("svc", RecoveryActionType.ROLLBACK)

    # patch _execute_action behaviour
    ers._execute_action = MagicMock(side_effect=[False, True])

    plan = [fail_action, rollback_action]
    success = all(ers.execute_recovery_action(a) for a in plan)
    assert success  # final state should be successful after rollback 