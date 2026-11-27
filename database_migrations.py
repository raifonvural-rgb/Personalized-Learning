"""
Version-controlled SQLite database migrations.

Each migration operates within a transaction
managed by the caller.
"""

from assignment_schema import create_assignment_schema

from activity_execution_schema import (
    create_activity_execution_schema,
)

from assignment_migration import (
    import_legacy_assignments,
    reconcile_orphaned_active_sessions,
    reconcile_migrated_active_sessions,
)


def verify_v2_migration_postconditions(connection):

    active_sessions = connection.execute(
        '''
        SELECT COUNT(*) AS record_count
        FROM learning_sessions
        WHERE status = 'ACTIVE'
          AND assignment_id IS NOT NULL
        '''
    ).fetchone()["record_count"]

    if active_sessions != 0:

        raise RuntimeError(
            "Legacy active assignment-bound sessions remain"
        )

    in_progress_assignments = connection.execute(
        '''
        SELECT COUNT(*) AS record_count
        FROM assignments
        WHERE status = 'IN_PROGRESS'
        '''
    ).fetchone()["record_count"]

    if in_progress_assignments != 0:

        raise RuntimeError(
            "Legacy in-progress assignments remain"
        )

    execution_states = connection.execute(
        '''
        SELECT COUNT(*) AS record_count
        FROM activity_execution_states
        '''
    ).fetchone()["record_count"]

    execution_rounds = connection.execute(
        '''
        SELECT COUNT(*) AS record_count
        FROM activity_execution_rounds
        '''
    ).fetchone()["record_count"]

    if execution_states != 0 or execution_rounds != 0:

        raise RuntimeError(
            "Unexpected legacy execution records"
        )

    foreign_key_violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if foreign_key_violations:

        raise RuntimeError(
            "Foreign key violations detected during migration"
        )

    return {
        "postconditions_verified": True,
        "remaining_active_assignment_sessions":
            active_sessions,
        "remaining_in_progress_assignments":
            in_progress_assignments,
        "execution_states": execution_states,
        "execution_rounds": execution_rounds,
        "foreign_key_violations":
            len(foreign_key_violations),
    }


def migrate_v1_to_v2(connection):
    """
    Introduce SQLite-based assignment management
    and persistent educational activity execution.

    Preserve existing performance records and
    migrate legacy assignment identities.
    """

    create_assignment_schema(connection)

    create_activity_execution_schema(connection)

    import_result = import_legacy_assignments(
        connection
    )

    reconciliation_result = (
        reconcile_orphaned_active_sessions(
            connection
        )
    )

    matched_reconciliation_result = (
        reconcile_migrated_active_sessions(
            connection
        )
    )

    verification_result = (
        verify_v2_migration_postconditions(
            connection
        )
    )

    return {
        "from_version": 1,
        "to_version": 2,
        **import_result,
        **reconciliation_result,
        **matched_reconciliation_result,
        **verification_result,
    }


MIGRATIONS = {
    1: migrate_v1_to_v2,
}


def migrate_database(
    connection,
    current_version,
    target_version
):
    """
    Apply sequential database schema migrations.

    The caller must provide an active write
    transaction and handle commit or rollback.
    """

    if not connection.in_transaction:
        raise RuntimeError(
            "Database migration requires a transaction"
        )

    if current_version < 1:
        raise ValueError(
            "Invalid current database schema version"
        )

    if current_version > target_version:
        raise RuntimeError(
            "Database downgrade is not supported"
        )

    version_record = connection.execute("""
        SELECT value
        FROM schema_metadata
        WHERE key = 'schema_version'
    """).fetchone()

    if (
        version_record is None
        or int(version_record["value"]) != current_version
    ):
        raise RuntimeError(
            "Database schema version mismatch"
        )

    results = []

    while current_version < target_version:

        migration = MIGRATIONS.get(current_version)

        if migration is None:
            raise RuntimeError(
                f"No migration available from "
                f"schema version {current_version}"
            )

        result = migration(connection)

        next_version = current_version + 1

        if result.get("to_version") != next_version:
            raise RuntimeError(
                "Unexpected migration target version"
            )

        update_result = connection.execute("""
            UPDATE schema_metadata
            SET value = ?
            WHERE key = 'schema_version'
              AND value = ?
        """, (
            str(next_version),
            str(current_version),
        ))

        if update_result.rowcount != 1:
            raise RuntimeError(
                "Schema version update failed"
            )

        results.append(result)

        current_version = next_version

    return results
