import logging

logger = logging.getLogger(__name__)


def validate_locations(df, issues):
    # Check if all locations are in Germany
    df = df[df["country"] != "Deutschland"]
    if not df.empty:
        issues["validation_errors"].append(
            {
                "validation_error_location_not_in_germany": f"Found {len(df['id'].to_list())} locations not in Germany",
                "LocationIds": df["id"].to_list(),
            }
        )


def validate_transactions(conn, issues):
    # transactions without any status events
    df = conn.execute(
        "SELECT id FROM transactions "
        "WHERE id NOT IN "
        "(SELECT transactionId "
        "FROM transaction_meter_values)"
    ).df()

    if not df.empty:
        issues["validation_errors"].append(
            {
                "validation_error_transaction_no_status_events": f"Found {len(df['id'].to_list())} transactions "
                f"with no corresponding status events",
                "transactionsIds": df["id"].to_list(),
            }
        )

    # transactions without charging_stopped status
    df = conn.execute(
        "SELECT id FROM transactions "
        "WHERE id NOT IN "
        "(SELECT transactionId "
        "FROM transaction_meter_values "
        "WHERE chargingStatusId = 1)"
    ).df()

    if not df.empty:
        issues["validation_errors"].append(
            {
                "validation_error_transaction_no_stopped_events": f"Found {len(df['id'].to_list())} transactions "
                f"with no charging_stopped status events",
                "transactionsIds": df["id"].to_list(),
            }
        )

    df = conn.execute("SELECT id FROM transactions " "WHERE kwhConsumed < 0").df()

    if not df.empty:
        issues["validation_errors"].append(
            {
                "validation_error_transaction_negative_kwh_consumed": f"Found {len(df['id'].to_list())} transactions "
                f"with negative kwhConsumed",
                "transactionsIds": df["id"].to_list(),
            }
        )
